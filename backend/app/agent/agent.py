import json
from typing import Tuple

from openai.types.chat import ChatCompletion

from ..config import settings
from . import tools
from .prompt import SYSTEM_PROMPT


def _run_llm_with_tools(messages: list) -> ChatCompletion:
    """
    OpenAI ChatCompletion을 tool calling 설정과 함께 실행.
    """
    client = settings.client
    return client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=tools.get_openai_tools_spec(),
        tool_choice="auto",
    )


def _extract_tool_call(response: ChatCompletion) -> Tuple[str, dict] | Tuple[None, None]:
    """
    첫 번째 tool call 추출. 없으면 (None, None) 반환.
    """
    choice = response.choices[0]
    message = choice.message

    if not message.tool_calls:
        return None, None

    tool_call = message.tool_calls[0]
    func = tool_call.function
    name = func.name

    try:
        args = json.loads(func.arguments or "{}")
    except json.JSONDecodeError:
        args = {}

    return name, args


def run_agent(question: str) -> Tuple[str, bool, dict]:
    """
    사용자 질문을 받아:
    1) LLM 호출 (tool calling 허용)
    2) 필요 시 web_search 도구 실행
    3) 검색 결과를 LLM에 다시 전달하여 최종 답변 생성

    반환: (answer, used_search, raw_model_dict)
    """
    messages: list = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    used_search = False

    # 1차 호출: 도구 사용 여부 결정
    first_response = _run_llm_with_tools(messages)
    name, args = _extract_tool_call(first_response)

    # 도구를 사용하지 않는 경우: 바로 답변 반환
    if not name:
        answer = first_response.choices[0].message.content or ""
        return answer, used_search, first_response.model_dump()

    # 현재는 web_search 하나만 지원
    tool_result_content = ""
    if name == "web_search":
        query = args.get("query") or question
        search_result = tools.web_search(query=query)
        used_search = True
        tool_result_content = json.dumps(search_result, ensure_ascii=False)

        # tool 응답 메시지 추가
        messages.append(first_response.choices[0].message.model_dump())
        messages.append(
            {
                "role": "tool",
                "tool_call_id": first_response.choices[0].message.tool_calls[0].id,
                "name": "web_search",
                "content": tool_result_content,
            }
        )

        # 2차 호출: 검색 결과를 바탕으로 최종 답변 생성
        second_response = settings.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
        )
        answer = second_response.choices[0].message.content or ""
        # raw 응답에는 두 번의 콜 모두를 포함시키기 위해 간단히 병합 정보 제공
        raw = {
            "first": first_response.model_dump(),
            "second": second_response.model_dump(),
        }
        return answer, used_search, raw

    # 정의되지 않은 도구 이름인 경우: 안전하게 에러 메시지
    safe_answer = (
        "요청된 도구를 사용할 수 없어 일반적인 정보만 기반으로 답변합니다. "
        "질문을 다시 시도하거나 관리자에게 문의해 주세요."
    )
    return safe_answer, used_search, first_response.model_dump()


