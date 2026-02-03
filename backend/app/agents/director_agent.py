"""LangGraph Director Agent - 스크립트 분석 및 콘티 블록 자동 생성"""
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re

from app.core.config import get_settings

logger = logging.getLogger(__name__)


# ==================== State 정의 ====================


class DirectorState(TypedDict):
    """Director Agent 상태"""
    script: str
    campaign_concept: Dict[str, str]  # {gender, tone, style, platform}
    target_duration: int
    keywords: List[str]
    visual_concepts: List[Dict[str, Any]]
    storyboard_blocks: List[Dict[str, Any]]
    background_suggestions: List[Dict[str, Any]]
    transition_effects: List[str]
    error: Optional[str]


# ==================== GPT-4 프롬프트 ====================


DIRECTOR_SYSTEM_PROMPT = """
당신은 전문 영상 감독(Director)입니다.
스크립트를 분석하여 시각적으로 매력적인 콘티 블록을 생성합니다.

역할:
1. 스크립트의 핵심 메시지와 감정 파악
2. 각 문장의 비주얼 컨셉 제안
3. 배경 이미지/영상 스타일 추천
4. 전환 효과 결정 (블록 간 감정 변화 고려)

출력 형식: JSON
"""


SCRIPT_ANALYSIS_PROMPT = """
다음 스크립트를 분석하여 의미 단위로 분할하고, 각 블록의 핵심 메시지와 감정을 추출하세요.

**스크립트:**
{script}

**캠페인 컨셉:**
- 성별: {gender}
- 톤: {tone}
- 스타일: {style}
- 플랫폼: {platform}

**목표 길이:** {target_duration}초

다음 JSON 형식으로 반환하세요:
{{
  "blocks": [
    {{
      "order": 0,
      "script": "첫 번째 문장",
      "emotion": "energetic | calm | serious | playful | inspiring",
      "key_message": "핵심 메시지 요약"
    }}
  ]
}}

**중요:**
- 의미가 완결된 문장 단위로 블록을 나눕니다 (문장을 절대 자르지 마세요)
- 각 블록은 완전한 생각이나 메시지를 담아야 합니다
- 블록 길이는 자연스럽게 결정됩니다 (5초~60초 모두 가능)
- 전체 블록을 합쳤을 때 목표 길이({target_duration}초)에 근접해야 합니다
"""


KEYWORD_EXTRACTION_PROMPT = """
다음 스크립트 블록에서 핵심 키워드를 추출하세요.

**스크립트:** {script}
**감정:** {emotion}

명사, 동사, 형용사 중심으로 3~5개의 키워드를 추출하여 JSON 배열로 반환하세요:
["키워드1", "키워드2", "키워드3"]
"""


VISUAL_CONCEPT_PROMPT = """
다음 스크립트 블록의 비주얼 컨셉을 생성하세요:

**스크립트:** {script}
**캠페인 컨셉:**
- 성별: {gender}
- 톤: {tone}
- 스타일: {style}
- 플랫폼: {platform}

**감정:** {emotion}
**키워드:** {keywords}

다음을 JSON으로 반환:
{{
  "mood": "energetic | calm | serious | playful | inspiring",
  "color_tone": "bright | dark | warm | cool | neutral",
  "background_style": "modern | vintage | natural | abstract | minimal",
  "background_prompt": "DALL-E 프롬프트 (영문, 50자 이내)",
  "transition_from_previous": "fade | slide | dissolve | zoom | none"
}}

**중요:**
- background_prompt는 영문으로 작성
- 캠페인 컨셉과 감정에 맞는 비주얼 제안
- 이전 블록과의 연속성 고려하여 전환 효과 결정
"""


BACKGROUND_SUGGESTION_PROMPT = """
다음 비주얼 컨셉에 맞는 배경을 추천하세요:

**비주얼 컨셉:** {visual_concept}
**키워드:** {keywords}

다음 우선순위로 배경을 추천:
1. AI 이미지 생성 (DALL-E 프롬프트)
2. 스톡 이미지 검색 키워드
3. 단색 배경 (색상 코드)

JSON 형식으로 반환:
{{
  "suggestions": [
    {{
      "type": "ai_generated | stock | solid_color",
      "priority": 1,
      "prompt": "DALL-E 프롬프트 (type=ai_generated일 때)",
      "search_keywords": ["키워드1", "키워드2"] (type=stock일 때),
      "color_hex": "#RRGGBB" (type=solid_color일 때),
      "rationale": "추천 이유"
    }}
  ]
}}
"""


# ==================== Agent Nodes ====================


def analyze_script(state: DirectorState) -> DirectorState:
    """
    스크립트 의미 분석 및 블록 분할

    GPT-4로 스크립트를 의미 단위로 분할하고,
    각 블록의 핵심 메시지와 감정을 추출합니다.
    """
    logger.info("Analyzing script...")

    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )

        prompt = SCRIPT_ANALYSIS_PROMPT.format(
            script=state["script"],
            gender=state["campaign_concept"].get("gender", "neutral"),
            tone=state["campaign_concept"].get("tone", "professional"),
            style=state["campaign_concept"].get("style", "modern"),
            platform=state["campaign_concept"].get("platform", "YouTube"),
            target_duration=state["target_duration"]
        )

        messages = [
            SystemMessage(content=DIRECTOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        response = llm.invoke(messages)
        result = json.loads(response.content)

        # blocks를 storyboard_blocks에 저장 (초기 구조)
        blocks = result.get("blocks", [])

        # 각 블록에 시간 할당 - DurationCalculator로 실제 시간 예측
        from app.services.duration_calculator import get_duration_calculator, Language
        duration_calc = get_duration_calculator(Language.KO)

        storyboard_blocks = []
        current_time = 0.0

        for block in blocks:
            # 실제 스크립트 길이 기반으로 시간 계산
            script_text = block["script"]

            # ✅ 스크립트 검증: 끊긴 문장 감지
            if script_text and len(script_text) > 10:
                # 마지막 문자가 문장 종결 기호가 아니면 경고
                last_char = script_text.strip()[-1]
                if last_char not in ['.', '!', '?', '。', '！', '？']:
                    logger.warning(f"⚠️ Block {block['order']} 스크립트가 끊겨 있을 수 있음: '{script_text[:50]}...'")

            predicted_duration = duration_calc.calculate(script_text)

            storyboard_blocks.append({
                "order": block["order"],
                "script": script_text,
                "start_time": current_time,
                "end_time": current_time + predicted_duration,
                "emotion": block.get("emotion", "neutral"),
                "key_message": block.get("key_message", ""),
                "keywords": [],
                "visual_concept": {},
                "background_type": "ai_generated",
                "background_prompt": None,
                "transition_effect": "fade",
                "subtitle_preset": "normal"
            })
            current_time += predicted_duration

        # 총 예상 길이가 목표를 초과하면 경고
        total_duration = sum(b["end_time"] - b["start_time"] for b in storyboard_blocks)
        target = state["target_duration"]
        if abs(total_duration - target) > target * 0.15:  # 15% 오차 초과
            logger.warning(f"⚠️ Duration mismatch: predicted={total_duration:.1f}s, target={target}s")
        else:
            logger.info(f"✅ Duration check: predicted={total_duration:.1f}s, target={target}s (within 15%)")

        state["storyboard_blocks"] = storyboard_blocks
        logger.info(f"Script analyzed: {len(storyboard_blocks)} blocks created")

    except Exception as e:
        logger.error(f"Script analysis failed: {e}")
        state["error"] = f"스크립트 분석 실패: {str(e)}"

    return state


def extract_keywords(state: DirectorState) -> DirectorState:
    """
    각 블록에서 핵심 키워드 추출

    명사, 동사, 형용사 중심으로 키워드를 추출합니다.
    """
    logger.info("Extracting keywords...")

    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.5,
            openai_api_key=settings.OPENAI_API_KEY
        )

        for block in state["storyboard_blocks"]:
            prompt = KEYWORD_EXTRACTION_PROMPT.format(
                script=block["script"],
                emotion=block.get("emotion", "neutral")
            )

            messages = [
                SystemMessage(content=DIRECTOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]

            response = llm.invoke(messages)
            keywords = json.loads(response.content)
            block["keywords"] = keywords if isinstance(keywords, list) else []

        logger.info("Keywords extracted for all blocks")

    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        state["error"] = f"키워드 추출 실패: {str(e)}"

    return state


def generate_visual_concepts(state: DirectorState) -> DirectorState:
    """
    각 블록의 비주얼 컨셉 생성

    분위기, 색감, 스타일, 전환 효과를 결정합니다.
    """
    logger.info("Generating visual concepts...")

    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )

        for block in state["storyboard_blocks"]:
            prompt = VISUAL_CONCEPT_PROMPT.format(
                script=block["script"],
                gender=state["campaign_concept"].get("gender", "neutral"),
                tone=state["campaign_concept"].get("tone", "professional"),
                style=state["campaign_concept"].get("style", "modern"),
                platform=state["campaign_concept"].get("platform", "YouTube"),
                emotion=block.get("emotion", "neutral"),
                keywords=", ".join(block["keywords"])
            )

            messages = [
                SystemMessage(content=DIRECTOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]

            response = llm.invoke(messages)
            visual_concept = json.loads(response.content)

            block["visual_concept"] = visual_concept
            block["background_prompt"] = visual_concept.get("background_prompt")
            block["transition_effect"] = visual_concept.get("transition_from_previous", "fade")

        logger.info("Visual concepts generated for all blocks")

    except Exception as e:
        logger.error(f"Visual concept generation failed: {e}")
        state["error"] = f"비주얼 컨셉 생성 실패: {str(e)}"

    return state


def suggest_backgrounds(state: DirectorState) -> DirectorState:
    """
    배경 자동 추천

    1순위: AI 이미지 생성 프롬프트
    2순위: 스톡 검색 키워드
    3순위: 단색 배경
    """
    logger.info("Suggesting backgrounds...")

    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )

        background_suggestions = []

        for block in state["storyboard_blocks"]:
            prompt = BACKGROUND_SUGGESTION_PROMPT.format(
                visual_concept=json.dumps(block["visual_concept"], ensure_ascii=False),
                keywords=", ".join(block["keywords"])
            )

            messages = [
                SystemMessage(content=DIRECTOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]

            response = llm.invoke(messages)
            suggestions = json.loads(response.content)

            # 1순위 추천을 블록에 적용
            top_suggestion = suggestions.get("suggestions", [])[0] if suggestions.get("suggestions") else None
            if top_suggestion:
                block["background_type"] = top_suggestion["type"]
                if top_suggestion["type"] == "ai_generated":
                    block["background_prompt"] = top_suggestion.get("prompt")
                elif top_suggestion["type"] == "stock":
                    block["background_prompt"] = ", ".join(top_suggestion.get("search_keywords", []))

            background_suggestions.append(suggestions)

        state["background_suggestions"] = background_suggestions
        logger.info("Background suggestions generated for all blocks")

    except Exception as e:
        logger.error(f"Background suggestion failed: {e}")
        state["error"] = f"배경 추천 실패: {str(e)}"

    return state


def assign_transitions(state: DirectorState) -> DirectorState:
    """
    전환 효과 자동 배정

    블록 간 감정 변화를 분석하여 적절한 전환 효과를 선택합니다.
    """
    logger.info("Assigning transition effects...")

    try:
        transition_effects = []

        for i, block in enumerate(state["storyboard_blocks"]):
            if i == 0:
                # 첫 번째 블록은 fade
                block["transition_effect"] = "fade"
            else:
                prev_block = state["storyboard_blocks"][i - 1]
                prev_emotion = prev_block.get("emotion", "neutral")
                curr_emotion = block.get("emotion", "neutral")

                # 감정 변화에 따른 전환 효과 결정
                if prev_emotion == curr_emotion:
                    # 동일 감정: fade (부드러운 전환)
                    block["transition_effect"] = "fade"
                elif prev_emotion in ["calm", "serious"] and curr_emotion in ["energetic", "playful"]:
                    # 조용함 → 활발함: zoom (에너지 증가)
                    block["transition_effect"] = "zoom"
                elif prev_emotion in ["energetic", "playful"] and curr_emotion in ["calm", "serious"]:
                    # 활발함 → 조용함: dissolve (에너지 감소)
                    block["transition_effect"] = "dissolve"
                else:
                    # 기타: slide (중립적 전환)
                    block["transition_effect"] = "slide"

            transition_effects.append(block["transition_effect"])

        state["transition_effects"] = transition_effects
        logger.info("Transition effects assigned to all blocks")

    except Exception as e:
        logger.error(f"Transition assignment failed: {e}")
        state["error"] = f"전환 효과 배정 실패: {str(e)}"

    return state


# ==================== LangGraph 구성 ====================


def create_director_graph() -> StateGraph:
    """
    Director Agent LangGraph 생성

    Returns:
        컴파일된 LangGraph
    """
    workflow = StateGraph(DirectorState)

    # 노드 추가
    workflow.add_node("analyze_script", analyze_script)
    workflow.add_node("extract_keywords", extract_keywords)
    workflow.add_node("generate_visual_concepts", generate_visual_concepts)
    workflow.add_node("suggest_backgrounds", suggest_backgrounds)
    workflow.add_node("assign_transitions", assign_transitions)

    # 시작점 설정
    workflow.set_entry_point("analyze_script")

    # 엣지 연결 (순차 실행)
    workflow.add_edge("analyze_script", "extract_keywords")
    workflow.add_edge("extract_keywords", "generate_visual_concepts")
    workflow.add_edge("generate_visual_concepts", "suggest_backgrounds")
    workflow.add_edge("suggest_backgrounds", "assign_transitions")
    workflow.add_edge("assign_transitions", END)

    return workflow.compile()


# ==================== Director Agent 인스턴스 ====================


_director_graph = None


def get_director_graph() -> StateGraph:
    """
    Director Agent 싱글톤 인스턴스 반환

    Returns:
        컴파일된 Director Graph
    """
    global _director_graph
    if _director_graph is None:
        _director_graph = create_director_graph()
        logger.info("Director Agent initialized")
    return _director_graph
