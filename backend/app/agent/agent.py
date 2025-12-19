from typing import Tuple

from ..config import settings
from .prompt import DEFAULT_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT


def _is_translation_request(question: str) -> bool:
    """
    질문이 '번역' 요청인지 간단한 키워드 기반으로 판별한다.
    """
    lowered = question.lower()
    keywords = [
        "번역해줘",
        "번역 해줘",
        "번역해 줘",
        "번역 부탁",
        "이 문서 번역",
        "이 파일 번역",
        "translate",
        "translation",
    ]
    return any(k in lowered for k in keywords)


def run_agent(question: str) -> Tuple[str, bool, dict]:
    """
    사용자 질문을 받아 OpenAI 모델에 단일 호출을 수행하고,
    응답 내용을 기반으로 웹 검색 사용 여부(used_search)를 추정한다.

    - 번역 요청인 경우: BASE + TRANSLATE 프롬프트 조합 사용
    - 그 외: BASE + ANALYZE 프롬프트 조합 사용

    반환: (answer, used_search, raw_model_dict)
    """
    system_prompt = (
        TRANSLATE_SYSTEM_PROMPT if _is_translation_request(question) else DEFAULT_SYSTEM_PROMPT
    )

    messages: list = [
        {"role": "system", "content": system_prompt},
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


