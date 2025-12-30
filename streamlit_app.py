import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_file" not in st.session_state:
    st.session_state.current_file = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# 헤더
st.title("🧠 만능 AI 에이전트")
st.caption("번역 · 요약 · 분석 · 일반 질문")

# 메인 화면: 파일 업로드 (상단에 배치)
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader(
        "📁 파일 업로드 (PDF 또는 TXT)",
        type=["pdf", "txt"],
        key="file_uploader",
        help="문서를 업로드하면 번역·분석이 가능합니다"
    )
    
    if uploaded_file:
        st.session_state.current_file = uploaded_file
        st.success(f"✅ **{uploaded_file.name}** 업로드 완료")
    else:
        st.session_state.current_file = None

with col2:
    st.write("")  # 공간 맞추기
    if st.session_state.current_file:
        if st.button("🗑️ 파일 제거", use_container_width=True):
            st.session_state.current_file = None
            st.rerun()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

st.divider()

# 채팅 메시지 표시
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "meta" in message and message["meta"]:
                st.caption(message["meta"])

# 채팅 입력 (Enter로 전송)
if prompt := st.chat_input("질문을 입력하세요 (Enter로 전송)"):
    # 사용자 메시지 추가
    user_content = prompt
    file_info = ""
    if st.session_state.current_file:
        file_info = f"📄 파일: {st.session_state.current_file.name}"
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_content,
        "meta": file_info if file_info else None
    })
    
    with st.chat_message("user"):
        st.markdown(user_content)
        if file_info:
            st.caption(file_info)
    
    # 대화 히스토리 빌드
    history_text = ""
    if st.session_state.conversation_history:
        history_text = "\n".join([
            f"{'사용자' if h['role'] == 'user' else 'AI'}: {h['content']}"
            for h in st.session_state.conversation_history
        ])
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                if st.session_state.current_file:
                    # 파일 + 질문
                    form_data = {"question": user_content or "이 문서 번역해줘"}
                    if history_text:
                        form_data["question"] = f"{history_text}\n\n새 질문: {form_data['question']}"
                    
                    files = {"file": (st.session_state.current_file.name, st.session_state.current_file.getvalue(), st.session_state.current_file.type)}
                    
                    response = requests.post(
                        f"{BACKEND_URL}/agent/file",
                        files=files,
                        data=form_data,
                        timeout=300,
                    )
                else:
                    # 질문만
                    question_for_agent = user_content
                    if history_text:
                        question_for_agent = f"{history_text}\n\n새 질문: {user_content}"
                    
                    response = requests.post(
                        f"{BACKEND_URL}/agent",
                        json={"question": question_for_agent},
                        timeout=300,
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("answer", "(빈 응답)")
                    used_search = result.get("used_search", False)
                    
                    st.markdown(answer)
                    
                    meta_text = "🔍 검색 활용" if used_search else "💬 일반 답변"
                    st.caption(meta_text)
                    
                    # AI 메시지 추가
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "meta": meta_text
                    })
                    
                    # 대화 히스토리 업데이트
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": user_content
                    })
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": answer
                    })
                else:
                    error_msg = f"오류: {response.status_code} - {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
            except Exception as e:
                error_msg = f"오류 발생: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
