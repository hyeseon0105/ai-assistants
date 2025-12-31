from typing import Optional

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(..., description="사용자 자연어 질문")


class AgentResponse(BaseModel):
    answer: str = Field(..., description="AI 에이전트의 최종 답변")
    used_search: bool = Field(
        False, description="웹 검색 도구 사용 여부 (하나 이상 호출되었는지 여부)"
    )
    raw_model: Optional[dict] = Field(
        default=None,
        description="디버깅용 원시 모델 응답(프로덕션에서는 보통 제외/마스킹)",
    )
    sources: Optional[List[Dict]] = Field(
        default=None,
        description="연구 모드에서 사용된 검색 결과 출처 목록",
    )


