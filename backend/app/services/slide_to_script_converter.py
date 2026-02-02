"""SlideToScriptConverter - 슬라이드 텍스트를 나레이션 스크립트로 자동 변환

주요 기능:
- 슬라이드 텍스트 → 자연스러운 나레이션 스크립트 생성 (LLM)
- 슬라이드별 예상 나레이션 시간 계산
- 전환 문구 자동 생성
- 스크립트 톤 조절 (전문적/친근함/교육적)
- Duration Calculator 재사용
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import logging

from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from app.services.duration_calculator import get_duration_calculator, Language

logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class ToneType(str, Enum):
    """나레이션 톤 타입"""
    PROFESSIONAL = "professional"  # 전문적이고 격식 있는
    FRIENDLY = "friendly"           # 친근하고 대화하는
    EDUCATIONAL = "educational"     # 교육적이고 설명적인


class SlideData(BaseModel):
    """슬라이드 데이터"""
    slide_number: int = Field(..., description="슬라이드 번호 (1부터 시작)")
    title: str = Field(..., description="슬라이드 제목")
    content: str = Field(..., description="슬라이드 본문 (불렛 포인트 포함)")
    notes: Optional[str] = Field(None, description="발표자 노트 (옵션)")


class ScriptConversionResponse(BaseModel):
    """스크립트 변환 결과"""
    full_script: str = Field(..., description="전체 나레이션 스크립트")
    slide_scripts: List[Dict[str, Any]] = Field(..., description="슬라이드별 스크립트")
    total_duration: float = Field(..., description="총 예상 시간 (초)")
    average_duration_per_slide: float = Field(..., description="슬라이드당 평균 시간 (초)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


# ==================== Prompt Templates ====================

SYSTEM_PROMPT_TEMPLATE = """당신은 프리젠테이션 나레이션 전문가입니다.
슬라이드의 텍스트를 자연스러운 나레이션 스크립트로 변환하세요.

**톤: {tone}**
- professional: 전문적이고 격식 있는 톤. 비즈니스 프리젠테이션, 학술 발표 등에 적합
- friendly: 친근하고 대화하는 톤. 일상적인 주제, 브이로그, 소셜 미디어 콘텐츠에 적합
- educational: 교육적이고 설명적인 톤. 튜토리얼, 강의, 교육 콘텐츠에 적합

**변환 지침:**
1. 슬라이드 텍스트를 문장으로 풀어서 자연스럽게 설명
2. 불렛 포인트는 문장으로 변환 (예: "- A - B - C" → "첫째 A, 둘째 B, 셋째 C입니다.")
3. 슬라이드 간 자연스러운 전환 문구 추가
4. 목표 시간: 슬라이드당 {target_duration}초
5. 언어: 한국어
6. 청중이 이해하기 쉽게 명확하고 간결하게 작성

**중요:**
- 슬라이드 제목과 내용을 모두 포함
- 전환 문구는 자연스럽게 (예: "다음으로", "그럼 이제", "계속해서")
- 너무 길거나 짧지 않게 균형 유지
"""

USER_PROMPT_TEMPLATE = """다음 슬라이드를 나레이션 스크립트로 변환해주세요:

{slides_text}

**요구사항:**
- 각 슬라이드를 자연스러운 나레이션으로 변환
- 슬라이드 간 전환 문구 추가
- 슬라이드당 목표 시간: {target_duration}초
- 톤: {tone}

**출력 형식:**
각 슬라이드에 대해 다음과 같이 작성:

[슬라이드 1]
나레이션 스크립트 내용...

[슬라이드 2]
나레이션 스크립트 내용...

(이런 식으로 계속)
"""


# ==================== SlideToScriptConverter ====================

class SlideToScriptConverter:
    """슬라이드 → 나레이션 스크립트 변환기"""

    def __init__(
        self,
        model_name: str = "claude-3-haiku-20240307",
        language: str = "ko"
    ):
        """
        Args:
            model_name: 사용할 LLM 모델 (Claude Haiku 권장)
            language: 언어 코드 (ko, en, ja, zh)
        """
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0.7,  # 창의적이면서도 일관성 유지
            max_tokens=4096
        )
        self.language = Language(language)
        self.duration_calculator = get_duration_calculator(self.language)
        logger.info(f"SlideToScriptConverter initialized with model={model_name}, language={language}")

    async def convert_slides_to_script(
        self,
        slides: List[SlideData],
        tone: ToneType = ToneType.PROFESSIONAL,
        target_duration_per_slide: float = 15.0
    ) -> ScriptConversionResponse:
        """
        슬라이드 → 나레이션 스크립트 변환

        Args:
            slides: 슬라이드 데이터 리스트
            tone: 나레이션 톤
            target_duration_per_slide: 슬라이드당 목표 시간 (초)

        Returns:
            ScriptConversionResponse: 변환 결과
        """
        logger.info(f"Converting {len(slides)} slides to script (tone={tone.value})")

        # 1. 슬라이드 텍스트 포맷팅
        slides_text = self._format_slides_for_prompt(slides)

        # 2. LLM 프롬프트 생성
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tone=tone.value,
            target_duration=target_duration_per_slide
        )
        user_prompt = USER_PROMPT_TEMPLATE.format(
            slides_text=slides_text,
            target_duration=target_duration_per_slide,
            tone=tone.value
        )

        # 3. LLM 호출
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)
        script_text = response.content

        # 4. 슬라이드별 스크립트 분리
        slide_scripts = self._parse_slide_scripts(script_text, len(slides))

        # 5. 슬라이드별 시간 계산
        for slide_script in slide_scripts:
            duration_info = self.duration_calculator.calculate(slide_script["script"])
            slide_script["estimated_duration"] = duration_info["duration"]
            slide_script["word_count"] = duration_info["word_count"]

        # 6. 전체 스크립트 및 시간
        full_script = "\n\n".join([s["script"] for s in slide_scripts])
        total_duration = sum([s["estimated_duration"] for s in slide_scripts])
        average_duration = total_duration / len(slides) if slides else 0

        logger.info(
            f"Conversion complete: total_duration={total_duration:.1f}s, "
            f"avg_duration={average_duration:.1f}s/slide"
        )

        return ScriptConversionResponse(
            full_script=full_script,
            slide_scripts=slide_scripts,
            total_duration=total_duration,
            average_duration_per_slide=average_duration,
            metadata={
                "tone": tone.value,
                "target_duration_per_slide": target_duration_per_slide,
                "slide_count": len(slides),
                "language": self.language.value
            }
        )

    def _format_slides_for_prompt(self, slides: List[SlideData]) -> str:
        """
        슬라이드를 LLM 프롬프트용 텍스트로 포맷팅

        Args:
            slides: 슬라이드 데이터 리스트

        Returns:
            포맷팅된 텍스트
        """
        formatted_lines = []

        for slide in slides:
            formatted_lines.append(f"=== 슬라이드 {slide.slide_number} ===")
            formatted_lines.append(f"제목: {slide.title}")
            formatted_lines.append(f"내용:\n{slide.content}")

            if slide.notes:
                formatted_lines.append(f"발표자 노트: {slide.notes}")

            formatted_lines.append("")  # 빈 줄 추가

        return "\n".join(formatted_lines)

    def _parse_slide_scripts(self, script_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """
        LLM 응답에서 슬라이드별 스크립트 분리

        Args:
            script_text: LLM 응답 텍스트
            expected_count: 예상 슬라이드 개수

        Returns:
            슬라이드별 스크립트 리스트
        """
        import re

        slide_scripts = []

        # [슬라이드 N] 패턴으로 분리
        pattern = r'\[슬라이드 (\d+)\]\s*\n(.*?)(?=\[슬라이드 \d+\]|$)'
        matches = re.findall(pattern, script_text, re.DOTALL)

        if matches:
            for slide_num_str, script_content in matches:
                slide_scripts.append({
                    "slide_number": int(slide_num_str),
                    "script": script_content.strip()
                })
        else:
            # 패턴 매칭 실패 시 전체를 하나의 스크립트로 처리
            logger.warning("Failed to parse slide scripts, using full text")
            slide_scripts.append({
                "slide_number": 1,
                "script": script_text.strip()
            })

        # 슬라이드 개수 검증
        if len(slide_scripts) != expected_count:
            logger.warning(
                f"Parsed {len(slide_scripts)} slides, expected {expected_count}"
            )

        return slide_scripts

    def generate_transition(
        self,
        current_slide_title: str,
        next_slide_title: str,
        tone: ToneType = ToneType.PROFESSIONAL
    ) -> str:
        """
        슬라이드 간 전환 문구 생성

        Args:
            current_slide_title: 현재 슬라이드 제목
            next_slide_title: 다음 슬라이드 제목
            tone: 나레이션 톤

        Returns:
            전환 문구
        """
        transitions = {
            ToneType.PROFESSIONAL: [
                f"다음으로 {next_slide_title}에 대해 살펴보겠습니다.",
                f"이어서 {next_slide_title}를 설명드리겠습니다.",
                f"계속해서 {next_slide_title}에 관한 내용입니다."
            ],
            ToneType.FRIENDLY: [
                f"그럼 이제 {next_slide_title}를 볼까요?",
                f"자, 다음은 {next_slide_title}입니다!",
                f"좋아요, 이제 {next_slide_title}로 넘어가볼게요."
            ],
            ToneType.EDUCATIONAL: [
                f"다음 단계로 {next_slide_title}를 배워보겠습니다.",
                f"이제 {next_slide_title}를 이해해봅시다.",
                f"계속해서 {next_slide_title}에 대해 알아보겠습니다."
            ]
        }

        # 톤별 전환 문구 중 랜덤 선택
        import random
        return random.choice(transitions[tone])

    def estimate_narration_duration(
        self,
        script: str
    ) -> float:
        """
        나레이션 예상 시간 계산

        Args:
            script: 나레이션 스크립트

        Returns:
            예상 시간 (초)
        """
        duration_info = self.duration_calculator.calculate(script)
        return duration_info["duration"]

    def adjust_script_length(
        self,
        script: str,
        target_duration: float,
        current_duration: Optional[float] = None
    ) -> str:
        """
        스크립트 길이 조정 (늘이기/줄이기)

        Args:
            script: 원본 스크립트
            target_duration: 목표 시간 (초)
            current_duration: 현재 시간 (None이면 자동 계산)

        Returns:
            조정된 스크립트
        """
        if current_duration is None:
            current_duration = self.estimate_narration_duration(script)

        # 목표 시간과의 차이 계산
        diff_ratio = target_duration / current_duration

        # ±10% 이내면 조정 불필요
        if 0.9 <= diff_ratio <= 1.1:
            logger.info(f"Script length is within acceptable range (diff={diff_ratio:.2%})")
            return script

        # 조정 필요 시 LLM으로 요청
        if diff_ratio < 1:
            # 줄이기
            instruction = f"다음 스크립트를 {int((1 - diff_ratio) * 100)}% 정도 짧게 줄여주세요. 핵심 내용은 유지하되 불필요한 부분을 제거하세요."
        else:
            # 늘이기
            instruction = f"다음 스크립트를 {int((diff_ratio - 1) * 100)}% 정도 길게 늘려주세요. 추가 설명이나 예시를 포함하세요."

        prompt = f"{instruction}\n\n원본 스크립트:\n{script}\n\n조정된 스크립트:"

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        adjusted_script = response.content.strip()

        logger.info(
            f"Adjusted script length: {current_duration:.1f}s → {target_duration:.1f}s "
            f"(diff={diff_ratio:.2%})"
        )

        return adjusted_script


# ==================== Utility Functions ====================

async def convert_slides_to_script(
    slides: List[Dict[str, Any]],
    tone: str = "professional",
    target_duration_per_slide: float = 15.0,
    language: str = "ko"
) -> Dict[str, Any]:
    """
    간편 함수: 슬라이드 → 나레이션 스크립트 변환

    Args:
        slides: 슬라이드 데이터 (딕셔너리 리스트)
        tone: 톤 (professional, friendly, educational)
        target_duration_per_slide: 슬라이드당 목표 시간 (초)
        language: 언어 코드

    Returns:
        변환 결과 (딕셔너리)
    """
    # 딕셔너리 → Pydantic 모델 변환
    slide_models = [SlideData(**slide) for slide in slides]

    converter = SlideToScriptConverter(language=language)
    result = await converter.convert_slides_to_script(
        slides=slide_models,
        tone=ToneType(tone),
        target_duration_per_slide=target_duration_per_slide
    )

    return result.model_dump()


def estimate_presentation_duration(
    slides: List[Dict[str, str]],
    target_duration_per_slide: float = 15.0,
    language: str = "ko"
) -> Dict[str, Any]:
    """
    간편 함수: 프리젠테이션 예상 시간 계산

    Args:
        slides: 슬라이드 데이터 (딕셔너리 리스트)
        target_duration_per_slide: 슬라이드당 목표 시간 (초)
        language: 언어 코드

    Returns:
        예상 시간 정보
    """
    calculator = get_duration_calculator(Language(language))

    total_duration = 0.0
    slide_durations = []

    for slide in slides:
        content = f"{slide.get('title', '')} {slide.get('content', '')}"
        duration_info = calculator.calculate(content)
        slide_durations.append(duration_info["duration"])
        total_duration += duration_info["duration"]

    return {
        "total_duration": total_duration,
        "slide_durations": slide_durations,
        "average_duration": total_duration / len(slides) if slides else 0,
        "target_total_duration": target_duration_per_slide * len(slides),
        "slide_count": len(slides)
    }
