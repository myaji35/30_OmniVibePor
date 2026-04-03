"""전략 수립 API — 비즈니스 목표 → 채널별 전략 → 콘텐츠 캘린더"""
import logging
from fastapi import APIRouter, HTTPException
from app.agents.strategy_agent import (
    StrategyInput,
    StrategyOutput,
    get_strategy_agent,
)

router = APIRouter(prefix="/strategy", tags=["Strategy"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=StrategyOutput)
async def generate_strategy(request: StrategyInput):
    """
    AI 전략 수립

    비즈니스 목표를 입력하면:
    1. 채널별 전략 (목표, 콘텐츠 유형, 게시 빈도, KPI)
    2. 주간 콘텐츠 캘린더 (토픽, 훅, CTA)
    3. Google Sheets 동기화 (선택)

    **예시 요청**:
    ```json
    {
      "business_goal": "3개월 내 신규 고객 100명 확보",
      "target_audience": "30~40대 직장인, 보험 관심자",
      "brand_name": "InsureGraph Pro",
      "industry": "insurance",
      "channels": ["youtube", "instagram", "blog"],
      "duration_weeks": 4,
      "tone": "professional"
    }
    ```
    """
    try:
        agent = get_strategy_agent()
        result = await agent.generate_strategy(request)
        logger.info(f"Strategy generated: {result.total_contents} contents for {result.brand_name}")
        return result
    except Exception as e:
        logger.error(f"Strategy generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"전략 생성 실패: {str(e)}")


@router.post("/preview")
async def preview_strategy(request: StrategyInput):
    """
    전략 미리보기 (LLM 없이 템플릿 기반)

    API 키 없이도 동작합니다. 기본 템플릿으로 전략 구조를 미리 확인할 수 있습니다.
    """
    try:
        agent = get_strategy_agent()
        fallback = agent._generate_fallback(request)

        return StrategyOutput(
            brand_name=request.brand_name,
            business_goal=request.business_goal,
            target_audience=request.target_audience,
            overall_strategy=fallback["overall_strategy"],
            channel_strategies=fallback["channel_strategies"],
            content_calendar=fallback["content_calendar"],
            total_contents=len(fallback["content_calendar"]),
            estimated_weekly_hours=len(fallback["content_calendar"]) / request.duration_weeks * 2,
            generated_at="preview",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
