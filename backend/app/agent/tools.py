from typing import Dict, Any, List


def web_search(query: str) -> Dict[str, Any]:
    """
    웹 검색 도구 (현재는 모의 구현).

    실제 구현 시:
    - 외부 검색 API 호출 (예: Bing, 자체 크롤러 등)
    - 결과 요약 및 정규화
    """
    # TODO: 실제 웹 검색 API 연동으로 교체
    return {
        "query": query,
        "results": [
            {
                "title": "예시 검색 결과 1",
                "url": "https://example.com/search-result-1",
                "snippet": "이것은 모의 웹 검색 결과 예시입니다. 실제 서비스에서는 외부 검색 엔진 결과가 들어갑니다.",
            },
            {
                "title": "예시 검색 결과 2",
                "url": "https://example.com/search-result-2",
                "snippet": "기업/의료 정보를 설명하는 예시 결과입니다. 실제 구현 시 교체해야 합니다.",
            },
        ],
    }


def get_openai_tools_spec() -> List[dict]:
    """
    OpenAI tool calling용 함수 스펙 정의.

    LLM이 `web_search`를 호출할 수 있도록 JSON 스키마를 제공한다.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "사용자 질문과 관련된 최신 웹 정보를 검색합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색할 질의어 (자연어 전체 문장 가능).",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }
    ]


