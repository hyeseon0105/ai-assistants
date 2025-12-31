"""
에이전트용 도구 모듈.

웹 검색 도구를 제공하여 Deep Research 기능을 지원합니다.
"""

from typing import List, Dict, Optional
import os

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class SearchResult:
    """검색 결과를 담는 데이터 클래스"""
    def __init__(self, title: str, url: str, content: str, score: Optional[float] = None):
        self.title = title
        self.url = url
        self.content = content
        self.score = score

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
        }


def web_search(query: str, max_results: int = 5) -> List[SearchResult]:
    """
    웹 검색을 수행하고 결과를 반환합니다.
    
    Tavily API가 설정되어 있으면 사용하고, 없으면 빈 리스트를 반환합니다.
    (OpenAI 모델의 내장 검색 기능은 프롬프트를 통해 활용)
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        
    Returns:
        SearchResult 리스트
    """
    if not TAVILY_AVAILABLE:
        return []
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        return []
    
    try:
        client = TavilyClient(api_key=tavily_key)
        # 검색 깊이를 "basic"으로 변경하여 속도 향상 (advanced는 느림)
        # max_results를 3개로 제한하여 처리 시간 단축
        response = client.search(
            query=query,
            max_results=min(max_results, 3),  # 최대 3개로 제한 (속도 향상)
            search_depth="basic",  # advanced -> basic으로 변경 (속도 향상, 2-3배 빠름)
        )
        
        results = []
        for result in response.get("results", []):
            results.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content", ""),
                score=result.get("score"),
            ))
        
        return results
    except Exception as e:
        # 에러 발생 시 빈 리스트 반환 (모델 내장 검색에 의존)
        print(f"웹 검색 오류: {e}")
        return []


def format_search_results(results: List[SearchResult]) -> str:
    """
    검색 결과를 프롬프트에 포함할 수 있는 형식으로 포맷팅합니다.
    
    Args:
        results: SearchResult 리스트
        
    Returns:
        포맷팅된 문자열
    """
    if not results:
        return ""
    
    formatted = "=== 웹 검색 결과 ===\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"[{i}] {result.title}\n"
        formatted += f"URL: {result.url}\n"
        formatted += f"내용: {result.content[:500]}...\n\n"  # 최대 500자
        
    return formatted
