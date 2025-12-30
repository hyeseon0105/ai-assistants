from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .agent.agent import run_agent
from .agent.schemas import AgentRequest, AgentResponse
from .files.loader import extract_text_from_upload


app = FastAPI(
    title="Web Search 기반 AI 에이전트",
    description="OpenAI API만 사용하는 기업/의료용 AI 에이전트 백엔드",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

# 정적 파일 서빙 (UI)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS 설정: 로컬에서 열어 둔 test.html 등이 백엔드에 요청할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "null"],  # file://에서 여는 경우 Origin이 "null"일 수 있음
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/")
async def root():
    """루트 경로에서 index.html로 리다이렉트"""
    from fastapi.responses import FileResponse, HTMLResponse
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(
            str(index_path),
            media_type="text/html",
            headers={"Cache-Control": "no-cache"}
        )
    return HTMLResponse(content="<h1>AI 에이전트 API</h1><p>index.html을 찾을 수 없습니다.</p><p><a href='/docs'>API 문서</a></p>")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/agent/file")
async def call_agent_with_file(
    file: UploadFile = File(...),
    question: str = Form("이 파일을 요약해줘"),
) -> dict:
    """
    업로드된 파일(PDF, TXT)을 기반으로 요약/분석/질문응답을 수행한다.
    """
    try:
        # 파일은 디스크에 저장하지 않고 메모리에서만 처리
        doc_text = await extract_text_from_upload(file)
    except ValueError as e:
        # 파일 형식/내용 관련 에러는 400으로 반환
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 내부 오류는 500
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {e}")

    combined_question = (
        "다음은 사용자가 업로드한 문서의 내용이다.\n"
        "이 문서를 기반으로 질문에 답하라.\n\n"
        "[문서 내용]\n"
        f"{doc_text}\n\n"
        f"질문: {question}"
    )

    try:
        answer, used_search, _raw = run_agent(combined_question)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 기반 에이전트 실행 중 오류가 발생했습니다: {e}",
        )

    return {
        "filename": file.filename,
        "answer": answer,
        "used_search": used_search,
    }

