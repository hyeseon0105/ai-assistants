import streamlit as st
import requests

BACKEND_URL = "https://ai-agent-backend-wvfl.onrender.com"

st.set_page_config(
    page_title="AI Agent",
    layout="wide",
)

# ======================
# Session State Init
# ======================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "current_file" not in st.session_state:
    st.session_state.current_file = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

# ======================
# Header
# ======================
st.title("🧠 AI 에이전트")
st.caption("문서 번역 · 분석 · 질문응답")

# ======================
# Messages
# ======================
if not st.session_state.messages:
    st.info("💬 질문을 입력하거나 파일을 업로드해 주세요")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            st.caption(msg["meta"])

# ======================
# 🔽 입력 영역 (파일 업로드 → 채팅 입력 순서)
# ======================

st.markdown("---")

# 📎 파일 업로드 (입력창 바로 위)
uploaded_file = st.file_uploader(
    "📎 파일 업로드 (PDF / TXT)",
    type=["pdf", "txt"],
    key=f"file_uploader_{st.session_state.file_uploader_key}",
    label_visibility="collapsed"
)

# 파일이 업로드되었고, 현재 파일이 없을 때만 저장
if uploaded_file:
    # 파일 크기 제한 (200MB)
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    
    # 이전 파일이 있으면 먼저 정리 (메모리 해제)
    if st.session_state.current_file:
        st.session_state.current_file = None
    
    # 새 파일 저장 및 크기 체크
    try:
        file_bytes = uploaded_file.getvalue()
        file_size = len(file_bytes)
        
        if file_size > MAX_FILE_SIZE:
            st.error(f"❌ 파일 크기가 너무 큽니다. 최대 200MB까지 업로드 가능합니다. (현재: {file_size / 1024 / 1024:.1f}MB)")
            del file_bytes  # 메모리 정리
            st.session_state.current_file = None
        else:
            st.session_state.current_file = {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "bytes": file_bytes,
            }
    except Exception as e:
        st.error(f"❌ 파일 읽기 오류: {str(e)}")
        st.session_state.current_file = None

# 파일 선택 상태 표시 + 제거 버튼
if st.session_state.current_file:
    col1, col2 = st.columns([8, 1])
    with col1:
        st.info(f"📄 {st.session_state.current_file['name']}")
    with col2:
        if st.button("❌", help="파일 제거", key="remove_file_btn"):
            st.session_state.current_file = None
            st.session_state.file_uploader_key += 1  # 위젯 리셋
            st.rerun()

# ======================
# Chat Input (항상 최하단)
# ======================
prompt = st.chat_input(
    "질문을 입력하세요... (예: 이 문서를 번역해줘, 위험한 조항만 뽑아줘)"
)

if prompt:
    question = prompt.strip()

    if not question and st.session_state.current_file:
        question = "이 파일을 분석해줘"

    if not question:
        st.warning("질문을 입력하세요.")
        st.stop()

    # 사용자 메시지 추가
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "meta": f"📄 {st.session_state.current_file['name']}"
        if st.session_state.current_file else None
    })

    st.session_state.pending_question = question
    st.rerun()

# ======================
# API Call (rerun 이후)
# ======================
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):

            try:
                history = "\n".join(
                    f"{'사용자' if h['role']=='user' else 'AI'}: {h['content']}"
                    for h in st.session_state.conversation_history
                )

                if st.session_state.current_file:
                    payload_question = (
                        f"{history}\n\n새 질문: {question}"
                        if history else question
                    )

                    # 파일 데이터 준비
                    file_data = st.session_state.current_file
                    files = {
                        "file": (
                            file_data["name"],
                            file_data["bytes"],
                            file_data["type"]
                        )
                    }
                    
                    # 타임아웃을 더 길게 설정 (큰 파일용)
                    # 연결 타임아웃 60초, 읽기 타임아웃 600초
                    response = requests.post(
                        f"{BACKEND_URL}/agent/file",
                        data={"question": payload_question},
                        files=files,
                        timeout=(60, 600)  # (connect timeout, read timeout)
                    )
                    
                    # 파일 데이터 참조 제거 (메모리 정리)
                    del files
                else:
                    payload_question = (
                        f"{history}\n\n새 질문: {question}"
                        if history else question
                    )

                    response = requests.post(
                        f"{BACKEND_URL}/agent",
                        json={"question": payload_question},
                        timeout=300
                    )

                # 응답 상태 확인
                if response.status_code != 200:
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", response.text)
                    except:
                        error_detail = response.text[:500]  # 너무 긴 경우 잘라냄
                    st.error(f"❌ 서버 오류 ({response.status_code}): {error_detail}")
                    st.stop()
                
                result = response.json()

                answer = result.get("answer", "(빈 응답)")
                used_search = result.get("used_search", False)

                st.markdown(answer)
                st.caption("🔍 검색 기반 답변" if used_search else "💬 일반 답변")

                # 메시지 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "meta": "🔍 검색 기반 답변" if used_search else "💬 일반 답변"
                })

                # 히스토리 저장
                st.session_state.conversation_history.extend([
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ])

                # 파일 자동 제거 (파일이 있을 때만)
                if st.session_state.current_file:
                    st.session_state.current_file = None
                    st.session_state.file_uploader_key += 1  # 위젯 리셋
                    st.rerun()

            except requests.exceptions.ConnectionError as e:
                error_msg = str(e)
                if "ConnectionResetError" in error_msg or "Connection aborted" in error_msg:
                    st.error(f"❌ 연결이 끊겼습니다. 파일이 너무 크거나 서버 문제일 수 있습니다. 다시 시도해주세요.")
                    st.info("💡 팁: 파일 크기를 줄이거나 잠시 후 다시 시도해주세요.")
                else:
                    st.error(f"❌ 연결 오류: {error_msg}")
            except requests.exceptions.Timeout as e:
                st.error(f"❌ 요청 시간 초과: 파일이 너무 크거나 서버 응답이 느립니다.")
                st.info("💡 팁: 더 작은 파일로 시도하거나 잠시 후 다시 시도해주세요.")
            except Exception as e:
                error_msg = str(e)
                # HTTP 에러인 경우 더 자세한 정보 표시
                if "400" in error_msg or "Client Error" in error_msg:
                    st.error(f"❌ 요청 오류: {error_msg}")
                elif "500" in error_msg or "Server Error" in error_msg:
                    st.error(f"❌ 서버 오류: {error_msg}")
                else:
                    st.error(f"❌ 오류 발생: {error_msg}")
