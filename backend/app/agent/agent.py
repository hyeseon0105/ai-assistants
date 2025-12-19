from typing import Tuple

from ..config import settings
from .prompt import SYSTEM_PROMPT


def run_agent(question: str) -> Tuple[str, bool, dict]:
    """
    사용자 질문을 받아 OpenAI 모델에 단일 호출을 수행하고,
    응답 내용을 기반으로 웹 검색 사용 여부(used_search)를 추정한다.

    반환: (answer, used_search, raw_model_dict)
    """
    messages: list = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    client = settings.client
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
    )

    answer = response.choices[0].message.content or ""

    # 간단한 휴리스틱: 답변에 검색/확인 관련 표현이 포함되어 있으면 used_search=True
    search_keywords = [
        "검색해 본 결과",
        "검색한 결과",
        "검색 결과",
        "공식 사이트",
        "공식 웹사이트",
        "공식 홈페이지",
        "확인 결과",
        "조사 결과",
    ]
    used_search = any(keyword in answer for keyword in search_keywords)

    return answer, used_search, response.model_dump()


