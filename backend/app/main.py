from fastapi import FastAPI, HTTPException

from .agent.agent import run_agent
from .agent.schemas import AgentRequest, AgentResponse


app = FastAPI(
    title="Web Search 기반 AI 에이전트",
    description="OpenAI API와 웹 검색 도구(mock)를 사용하는 기업/의료용 AI 에이전트 백엔드",
    version="0.1.0",
)


@app.post("/agent", response_model=AgentResponse)
async def call_agent(request: AgentRequest) -> AgentResponse:
    """
    AI 에이전트에 질문을 전달하고 최종 답변을 반환합니다.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question 필드는 비어 있을 수 없습니다.")

    try:
        answer, used_search, raw = run_agent(question)
    except Exception as e:  # 최소한의 에러 핸들링
        raise HTTPException(status_code=500, detail=f"에이전트 실행 중 오류가 발생했습니다: {e}")

    return AgentResponse(answer=answer, used_search=used_search, raw_model=raw)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


