from typing import TypedDict, Tuple, Literal

from langgraph.graph import StateGraph, END

from ..config import settings
from .prompt import DEFAULT_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT


class AgentState(TypedDict):
    """에이전트 상태 정의"""
    question: str
    mode: Literal["translate", "general"]
    system_prompt: str
    messages: list
    answer: str
    used_search: bool
    raw_response: dict


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


def detect_mode(state: AgentState) -> AgentState:
    """번역 모드인지 일반 모드인지 판단"""
    is_translate = _is_translation_request(state["question"])
    # 상태 업데이트 (새 딕셔너리 반환)
    new_state = state.copy()
    new_state["mode"] = "translate" if is_translate else "general"
    new_state["system_prompt"] = (
        TRANSLATE_SYSTEM_PROMPT if is_translate else DEFAULT_SYSTEM_PROMPT
    )
    return new_state


def call_llm(state: AgentState) -> AgentState:
    """OpenAI LLM 호출"""
    # OpenAI API 형식으로 메시지 변환
    openai_messages = [
        {"role": "system", "content": state["system_prompt"]},
        {"role": "user", "content": state["question"]},
    ]

    client = settings.client
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=openai_messages,
    )

    answer = response.choices[0].message.content or ""
    
    # 상태 업데이트 (새 딕셔너리 반환)
    new_state = state.copy()
    new_state["answer"] = answer
    new_state["raw_response"] = response.model_dump()
    new_state["messages"] = openai_messages

    return new_state


def detect_search_usage(state: AgentState) -> AgentState:
    """답변 내용 기반으로 웹 검색 사용 여부 추정"""
    answer = state["answer"]
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
    # 상태 업데이트 (새 딕셔너리 반환)
    new_state = state.copy()
    new_state["used_search"] = any(keyword in answer for keyword in search_keywords)
    return new_state


# LangGraph 그래프 구성
def create_agent_graph() -> StateGraph:
    """에이전트 워크플로우 그래프 생성"""
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("detect_mode", detect_mode)
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("detect_search", detect_search_usage)

    # 엣지 정의
    workflow.set_entry_point("detect_mode")
    workflow.add_edge("detect_mode", "call_llm")
    workflow.add_edge("call_llm", "detect_search")
    workflow.add_edge("detect_search", END)

    return workflow.compile()


# 그래프 인스턴스 생성 (모듈 레벨에서 한 번만)
_agent_graph = None


def get_agent_graph() -> StateGraph:
    """에이전트 그래프 싱글톤 반환"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


def run_agent(question: str) -> Tuple[str, bool, dict]:
    """
    사용자 질문을 받아 LangGraph 기반 에이전트를 실행하고 결과를 반환한다.

    - 번역 요청인 경우: BASE + TRANSLATE 프롬프트 조합 사용
    - 그 외: BASE + ANALYZE 프롬프트 조합 사용

    반환: (answer, used_search, raw_model_dict)
    """
    graph = get_agent_graph()

    # 초기 상태
    initial_state: AgentState = {
        "question": question,
        "mode": "general",  # detect_mode에서 설정됨
        "system_prompt": "",
        "messages": [],
        "answer": "",
        "used_search": False,
        "raw_response": {},
    }

    # 그래프 실행
    final_state = graph.invoke(initial_state)

    return (
        final_state["answer"],
        final_state["used_search"],
        final_state["raw_response"],
    )
