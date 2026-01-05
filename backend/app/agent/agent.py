from typing import TypedDict, Tuple, Literal, List, Dict, Optional
from langgraph.graph import StateGraph, END

from ..config import settings
from .prompt import DEFAULT_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT, RESEARCH_SYSTEM_PROMPT
from .tools import web_search, format_search_results, SearchResult


class AgentState(TypedDict):
    """에이전트 상태 정의"""
    question: str
    mode: Literal["translate", "general", "research"]
    system_prompt: str
    messages: list
    answer: str
    used_search: bool
    raw_response: dict
    search_results: List[Dict]  # 검색 결과 저장
    research_iterations: int  # 연구 반복 횟수
    max_iterations: int  # 최대 반복 횟수


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


def _is_research_request(question: str) -> bool:
    """
    질문이 '연구' 또는 '심층 분석' 요청인지 판별한다.
    명시적인 키워드만 감지하여 불필요한 연구 모드 진입을 방지.
    """
    lowered = question.lower()
    # 명시적인 연구 요청 키워드만 감지 (더 엄격하게)
    research_keywords = [
        "연구해줘",
        "조사해줘",
        "리서치",
        "research",
        "deep research",
        "보고서 작성",
        "보고서 만들어",
        "report",
        "심층 연구",
        "상세 연구",
    ]
    # "분석해줘", "상세히", "자세히" 같은 일반적인 키워드는 제외
    return any(k in lowered for k in research_keywords)


def detect_mode(state: AgentState) -> AgentState:
    """번역/연구/일반 모드 판단"""
    try:
        question = state["question"]
        is_translate = _is_translation_request(question)
        is_research = _is_research_request(question)
        
        # TypedDict는 copy()가 없으므로 dict()로 변환
        new_state = dict(state)
        if is_translate:
            new_state["mode"] = "translate"
            new_state["system_prompt"] = TRANSLATE_SYSTEM_PROMPT
        elif is_research:
            new_state["mode"] = "research"
            new_state["system_prompt"] = RESEARCH_SYSTEM_PROMPT
            new_state["max_iterations"] = 2  # 최대 2회 검색 반복 (성능 최적화)
            new_state["research_iterations"] = 0
            new_state["search_results"] = []
        else:
            new_state["mode"] = "general"
            new_state["system_prompt"] = DEFAULT_SYSTEM_PROMPT
        
        return new_state
    except Exception as e:
        # 에러 발생 시 기본 상태 반환
        new_state = dict(state)
        new_state["mode"] = "general"
        new_state["system_prompt"] = DEFAULT_SYSTEM_PROMPT
        return new_state


def perform_search(state: AgentState) -> AgentState:
    """웹 검색 수행 (연구 모드에서만 사용)"""
    try:
        question = state["question"]
        iterations = state.get("research_iterations", 0)
        max_iter = state.get("max_iterations", 3)
        
        # TypedDict는 copy()가 없으므로 dict()로 변환
        new_state = dict(state)
        
        # 최대 반복 횟수 체크
        if iterations >= max_iter:
            return new_state
        
        # 검색 수행
        search_query = question if iterations == 0 else f"{question} 상세 정보"
        results = web_search(search_query, max_results=5)
        
        # 검색 결과 저장
        existing_results = new_state.get("search_results", [])
        for result in results:
            existing_results.append(result.to_dict())
        new_state["search_results"] = existing_results
        new_state["research_iterations"] = iterations + 1
        new_state["used_search"] = True
        
        return new_state
    except Exception as e:
        # 검색 실패 시 기존 상태 유지
        return dict(state)


def call_llm(state: AgentState) -> AgentState:
    """OpenAI LLM 호출"""
    try:
        question = state["question"]
        system_prompt = state["system_prompt"]
        mode = state.get("mode", "general")
        
        # 연구 모드인 경우 검색 결과를 포함
        messages = [{"role": "system", "content": system_prompt}]
        
        if mode == "research" and state.get("search_results"):
            # 검색 결과를 컨텍스트에 추가
            search_context = format_search_results([
                SearchResult(**r) for r in state["search_results"]
            ])
            user_content = f"{search_context}\n\n질문: {question}"
        else:
            user_content = question
        
        messages.append({"role": "user", "content": user_content})
        
        client = settings.client
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
        )

        answer = response.choices[0].message.content or ""
        
        # TypedDict는 copy()가 없으므로 dict()로 변환
        new_state = dict(state)
        new_state["answer"] = answer
        new_state["raw_response"] = response.model_dump()
        new_state["messages"] = messages

        return new_state
    except Exception as e:
        # LLM 호출 실패 시 에러 메시지 반환
        new_state = dict(state)
        new_state["answer"] = f"오류가 발생했습니다: {str(e)}"
        new_state["raw_response"] = {}
        new_state["messages"] = []
        return new_state


def should_continue_research(state: AgentState) -> str:
    """
    연구를 계속할지 결정하는 조건부 엣지 함수.
    연구 모드에서만 사용되며, 추가 검색이 필요한지 판단합니다.
    성능 최적화: 최대 2회 검색으로 제한하고, 빠르게 종료 조건 추가.
    """
    mode = state.get("mode", "general")
    if mode != "research":
        return "end"
    
    iterations = state.get("research_iterations", 0)
    max_iter = state.get("max_iterations", 2)  # 3회 -> 2회로 감소
    
    # 최대 반복 횟수에 도달한 경우 종료
    if iterations >= max_iter:
        return "end"
    
    # 첫 번째 검색이 아직 수행되지 않은 경우 검색 수행
    if iterations == 0:
        return "search"
    
    # 첫 검색 후 답변을 확인하여 충분성 판단
    answer = state.get("answer", "")
    
    # 충분히 긴 답변이거나, 구조화된 보고서 형식이 있으면 종료
    if len(answer) > 1500:  # 2000 -> 1500으로 낮춤 (더 빠른 종료)
        return "end"
    
    # 보고서 형식 키워드가 있으면 종료 (이미 충분한 정보)
    report_keywords = ["## 요약", "## 주요 발견사항", "## 상세 분석", "## 출처"]
    if any(keyword in answer for keyword in report_keywords):
        return "end"
    
    # 추가 검색이 필요한 경우만 수행
    return "search"


def should_search_first(state: AgentState) -> str:
    """
    연구 모드에서 첫 검색을 먼저 수행할지 결정하는 조건부 엣지 함수.
    """
    mode = state.get("mode", "general")
    if mode == "research":
        iterations = state.get("research_iterations", 0)
        if iterations == 0:
            return "search"  # 첫 검색 수행
    return "llm"  # 바로 LLM 호출


def detect_search_usage(state: AgentState) -> AgentState:
    """답변 내용 기반으로 웹 검색 사용 여부 추정"""
    try:
        answer = state.get("answer", "")
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
        # TypedDict는 copy()가 없으므로 dict()로 변환
        new_state = dict(state)
        # 실제 검색을 수행했거나, 답변에 검색 키워드가 포함된 경우
        new_state["used_search"] = state.get("used_search", False) or any(
            keyword in answer for keyword in search_keywords
        )
        return new_state
    except Exception as e:
        # 에러 발생 시 기존 상태 유지
        return dict(state)


def create_agent_graph():
    """에이전트 워크플로우 그래프 생성"""
    try:
        workflow = StateGraph(AgentState)

        # 노드 추가
        workflow.add_node("detect_mode", detect_mode)
        workflow.add_node("perform_search", perform_search)
        workflow.add_node("call_llm", call_llm)
        workflow.add_node("detect_search", detect_search_usage)

        # 엣지 정의
        workflow.set_entry_point("detect_mode")
        
        # 모드 감지 후 연구 모드면 검색부터, 아니면 바로 LLM 호출
        workflow.add_conditional_edges(
            "detect_mode",
            should_search_first,
            {
                "search": "perform_search",
                "llm": "call_llm",
            }
        )
        
        # 검색 후 LLM 호출
        workflow.add_edge("perform_search", "call_llm")
        
        # LLM 호출 후 연구 모드면 추가 검색 여부 판단
        workflow.add_conditional_edges(
            "call_llm",
            should_continue_research,
            {
                "search": "perform_search",
                "end": "detect_search",
            }
        )
        
        # 최종 종료
        workflow.add_edge("detect_search", END)

        return workflow.compile()
    except Exception as e:
        raise RuntimeError(f"에이전트 그래프 생성 중 오류가 발생했습니다: {str(e)}") from e


# 그래프 인스턴스 생성 (모듈 레벨에서 한 번만)
_agent_graph = None


def get_agent_graph() -> StateGraph:
    """에이전트 그래프 싱글톤 반환"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


def run_agent(question: str) -> Tuple[str, bool, dict, Optional[List[Dict]]]:
    """
    사용자 질문을 받아 LangGraph 기반 에이전트를 실행하고 결과를 반환한다.

    - 번역 요청인 경우: BASE + TRANSLATE 프롬프트 조합 사용
    - 연구 요청인 경우: BASE + RESEARCH 프롬프트 조합 사용 (다단계 검색)
    - 그 외: BASE + ANALYZE 프롬프트 조합 사용

    반환: (answer, used_search, raw_model_dict, sources)
    """
    try:
        graph = get_agent_graph()

        # 초기 상태
        initial_state: AgentState = {
            "question": question.strip(),
            "mode": "general",  # detect_mode에서 설정됨
            "system_prompt": "",
            "messages": [],
            "answer": "",
            "used_search": False,
            "raw_response": {},
            "search_results": [],
            "research_iterations": 0,
            "max_iterations": 2,  # 기본값도 2회로 설정
        }

        # 그래프 실행
        final_state = graph.invoke(initial_state)

        # 소스 정보 추출 (연구 모드인 경우)
        sources = None
        if final_state.get("search_results"):
            sources = final_state["search_results"]

        # 안전하게 값 추출
        answer = final_state.get("answer", "답변을 생성할 수 없습니다.")
        used_search = final_state.get("used_search", False)
        raw_response = final_state.get("raw_response", {})

        return (
            answer,
            used_search,
            raw_response,
            sources,
        )
    except Exception as e:
        # 에러 발생 시 기본값 반환
        error_msg = f"에이전트 실행 중 오류가 발생했습니다: {str(e)}"
        return (
            error_msg,
            False,
            {},
            None,
        )
