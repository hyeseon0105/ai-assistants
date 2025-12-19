"""
에이전트에서 사용하는 최종 System Prompt 정의 모듈.

실제 규칙과 톤은 `backend/app/prompts/` 아래의 모듈들에서 정의하며,
이 파일은 그 프롬프트들을 조합해 단일 SYSTEM_PROMPT로 노출하는 역할만 담당한다.
"""

from ..prompts.base import BASE_PROMPT
from ..prompts.translate import TRANSLATE_PROMPT
from ..prompts.analyze import ANALYZE_PROMPT


# 기본 모드: 일반 질문, 요약/분석 중심
DEFAULT_SYSTEM_PROMPT = "\n\n".join(
    [
        BASE_PROMPT,
        ANALYZE_PROMPT,
    ]
).strip()

# 번역 모드: 번역 품질 고정을 위해 번역 전용 규칙만 포함
TRANSLATE_SYSTEM_PROMPT = "\n\n".join(
    [
        BASE_PROMPT,
        TRANSLATE_PROMPT,
    ]
).strip()


# 하위 호환성을 위해 기본 프롬프트를 SYSTEM_PROMPT로 노출
SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT



