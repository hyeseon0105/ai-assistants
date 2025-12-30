AI 에이전트 - 문서 번역 및 분석 플랫폼

OpenAI API를 활용하여 문서 번역, 요약, 분석 및 질문 응답 기능을 구현한 학습 및 과제용 AI 에이전트 프로젝트입니다.

🎯 프로젝트 소개

이 프로젝트는 OpenAI API를 활용한 AI 에이전트 구조를 직접 구현하고 배포해보기 위한 과제 수행 목적으로 제작되었습니다.

Streamlit 기반의 프론트엔드와 FastAPI 기반의 백엔드를 분리하여 구성하였으며,
파일 업로드(PDF/TXT), 문서 기반 질문 응답, 번역 및 요약 기능을 포함한 AI 서비스의 기본적인 흐름을 실습하는 데 중점을 두었습니다.

❓ 왜 만들었나요?

이 프로젝트는 개인 과제 수행 및 학습을 목적으로 제작되었습니다.

주요 목표는 다음과 같습니다:

AI 에이전트 기본 구조 이해: LLM을 활용한 질문 응답 흐름 구현

문서 기반 처리 실습: PDF/TXT 파일 업로드 및 문서 내용 기반 질의 응답

프롬프트 분리 및 관리: 번역, 분석 등 목적별 프롬프트 구조화

프론트엔드–백엔드 연동 경험: Streamlit ↔ FastAPI API 통신

실제 배포 경험: Streamlit Cloud 및 Render를 활용한 배포 실습

본 프로젝트는 학습 및 실습 목적의 데모 프로젝트이며,
실제 기업/의료 환경에서의 사용을 전제로 하지 않습니다.

✨ 주요 기능

1. 문서 번역 (데모)

번역 요청 키워드 기반 자동 감지

PDF/TXT 문서 텍스트 번역

프롬프트 기반 문서 타입 구분 (실험적)

2. 문서 분석 및 요약

PDF/TXT 파일 업로드 지원

문서 내용 기반 질문 응답

요약 및 핵심 내용 추출

3. 일반 질문 응답

대화형 UI (Streamlit)

대화 히스토리 유지

검색 기반 응답 여부 표시

## 🛠 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangGraph**: 에이전트 오케스트레이션 및 워크플로우 관리
- **OpenAI API**: GPT 모델을 통한 자연어 처리
- **pypdf**: PDF 텍스트 추출
- **uvicorn**: ASGI 서버

### Frontend
- **Streamlit**: Python 기반 웹 애플리케이션 프레임워크
- **HTML/CSS/JavaScript**: 정적 웹 인터페이스 (FastAPI 서빙)

### 기타
- **python-dotenv**: 환경 변수 관리
- **requests/httpx**: HTTP 클라이언트

## 📁 프로젝트 구조

```
ai-assistants/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── agent.py          # LangGraph 에이전트 구현
│   │   │   ├── prompt.py         # 시스템 프롬프트 관리
│   │   │   ├── schemas.py        # Pydantic 모델
│   │   │   └── tools.py          # 도구 정의 (현재 미사용)
│   │   ├── files/
│   │   │   └── loader.py         # PDF/TXT 파일 처리
│   │   ├── prompts/
│   │   │   ├── base.py           # 기본 프롬프트 (안전 정책, 일반 규칙)
│   │   │   ├── translate.py      # 번역 전용 프롬프트
│   │   │   └── analyze.py        # 분석/요약 프롬프트
│   │   ├── config.py             # 설정 관리 (OpenAI 클라이언트)
│   │   └── main.py               # FastAPI 애플리케이션
│   ├── static/
│   │   └── index.html            # 정적 웹 UI
│   └── requirements.txt          # Python 의존성
├── streamlit_app.py              # Streamlit 프론트엔드
├── test.html                     # 테스트용 HTML 파일
└── README.md                     # 프로젝트 문서
```

## 🚀 설치 및 실행

### 사전 요구사항

- Python 3.10 이상
- OpenAI API Key

### 1. 저장소 클론

```bash
git clone <repository-url>
cd ai-assistants
```

### 2. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
# Backend 의존성
cd backend
pip install -r requirements.txt

# Streamlit (프론트엔드)
pip install streamlit
```

### 4. 환경 변수 설정

`backend/.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

`.env.example` 파일을 참고할 수 있습니다.

### 5. Backend 실행

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend는 `http://localhost:8000`에서 실행됩니다.

### 6. Frontend 실행

#### Streamlit 앱 실행

```bash
streamlit run streamlit_app.py
```

Streamlit 앱은 `http://localhost:8501`에서 실행됩니다.

#### 정적 HTML UI 사용

Backend를 실행한 후 브라우저에서 `http://localhost:8000`에 접속하세요.

## 📖 사용 방법

### Streamlit 앱 사용

1. Streamlit 앱 실행
2. 파일 업로드 (선택사항): PDF 또는 TXT 파일을 업로드
3. 질문 입력: 예) "이 문서를 번역해줘", "위험한 조항만 뽑아줘"
4. Enter 키로 전송
5. 결과 확인: AI 응답이 채팅 형태로 표시됩니다

### API 사용

#### 일반 질문

```bash
curl -X POST "http://localhost:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{"question": "인공지능이란 무엇인가요?"}'
```

#### 파일 업로드 및 질문

```bash
curl -X POST "http://localhost:8000/agent/file" \
  -F "file=@document.pdf" \
  -F "question=이 문서를 번역해줘"
```

## 📚 API 문서

Backend 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` (비활성화됨)

### 주요 엔드포인트

#### `POST /agent`
일반 질문에 대한 답변을 반환합니다.

**Request Body:**
```json
{
  "question": "질문 내용"
}
```

**Response:**
```json
{
  "answer": "AI 응답",
  "used_search": false,
  "raw_model": {...}
}
```

#### `POST /agent/file`
파일 업로드 및 파일 기반 질문 응답을 제공합니다.

**Form Data:**
- `file`: PDF 또는 TXT 파일
- `question`: 질문 내용 (기본값: "이 파일을 요약해줘")

**Response:**
```json
{
  "filename": "document.pdf",
  "answer": "AI 응답",
  "used_search": false
}
```

#### `GET /health`
서버 상태를 확인합니다.

**Response:**
```json
{
  "status": "ok"
}
```

## 🔐 환경 변수

| 변수명 | 설명 | 필수 | 기본값 |
|--------|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ | - |
| `OPENAI_MODEL` | 사용할 OpenAI 모델 | ❌ | `gpt-4o-mini` |

## 🎨 주요 특징

### 1. 자동 모드 전환

에이전트는 질문 내용을 분석하여 자동으로 모드를 전환합니다:

- **번역 모드**: "번역해줘", "translate" 등의 키워드 감지 시 번역 전용 프롬프트 사용
- **일반 모드**: 그 외의 경우 일반 분석/요약 프롬프트 사용

### 2. 프롬프트 모듈화

프롬프트는 목적에 따라 분리되어 관리됩니다:

- `base.py`: 공통 규칙, 안전 정책, 의료/기업 원칙
- `translate.py`: 번역 품질 고정, 문서 타입 감지, 의료 용어 관리
- `analyze.py`: 문서 분석, 요약, 핵심 내용 추출

### 3. LangGraph 기반 워크플로우

에이전트는 LangGraph를 사용하여 구조화된 워크플로우로 실행됩니다:

```
입력 질문
  ↓
모드 감지 (번역/일반)
  ↓
시스템 프롬프트 선택
  ↓
LLM 호출
  ↓
검색 사용 여부 감지
  ↓
최종 응답 반환
```

## 🚢 배포

### Render 배포 (Backend)

1. Render 대시보드에서 새 Web Service 생성
2. GitHub 저장소 연결
3. 빌드 명령: `cd backend && pip install -r requirements.txt`
4. 시작 명령: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 환경 변수 설정: `OPENAI_API_KEY`, `OPENAI_MODEL`

### Streamlit Cloud 배포 (Frontend)

1. Streamlit Cloud에 GitHub 저장소 연결
2. 메인 파일: `streamlit_app.py`
3. 환경 변수 설정: `BACKEND_URL` (Render 배포 URL)



---


