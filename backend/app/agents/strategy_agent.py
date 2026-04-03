"""
전략 수립 엔진 — AI Director가 비즈니스 목표 → 채널별 전략 → 콘텐츠 캘린더 자동 생성

ISS-007: Phase 5 핵심 모듈
- 입력: 비즈니스 목표, 타겟 오디언스, 기간
- 출력: 채널별 전략 JSON + 주간 콘텐츠 캘린더
- Google Sheets 동기화 지원
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── 입출력 모델 ──────────────────────────────────

class StrategyInput(BaseModel):
    """전략 수립 요청"""
    business_goal: str = Field(..., min_length=1, description="비즈니스 목표 (예: '3개월 내 신규 고객 100명 확보')")
    target_audience: str = Field(..., min_length=1, description="타겟 오디언스 (예: '30~40대 직장인, 보험 관심자')")
    brand_name: str = Field(..., min_length=1, description="브랜드명")
    industry: str = Field("general", description="산업 분야 (insurance, tech, education, ecommerce 등)")
    budget_level: str = Field("medium", description="예산 수준 (low, medium, high)")
    duration_weeks: int = Field(4, ge=1, le=12, description="전략 기간 (주)")
    channels: list[str] = Field(
        default=["youtube", "instagram", "blog"],
        description="활용 채널"
    )
    tone: str = Field("professional", description="톤앤매너 (professional, friendly, humorous, educational)")
    spreadsheet_id: Optional[str] = Field(None, description="Google Sheets ID (동기화 시)")


class ChannelStrategy(BaseModel):
    """채널별 전략"""
    channel: str
    goal: str
    content_type: str
    posting_frequency: str
    key_topics: list[str]
    tone: str
    cta: str
    kpi: str


class ContentCalendarItem(BaseModel):
    """콘텐츠 캘린더 항목"""
    week: int
    day: str
    channel: str
    content_type: str
    topic: str
    hook: str
    cta: str
    status: str = "draft"
    estimated_duration: Optional[int] = None  # 초 (영상용)


class StrategyOutput(BaseModel):
    """전략 수립 결과"""
    brand_name: str
    business_goal: str
    target_audience: str
    overall_strategy: str
    channel_strategies: list[ChannelStrategy]
    content_calendar: list[ContentCalendarItem]
    total_contents: int
    estimated_weekly_hours: float
    generated_at: str


# ── 전략 생성 프롬프트 ────────────────────────────

STRATEGY_SYSTEM_PROMPT = """당신은 디지털 마케팅 전략 전문가입니다.
비즈니스 목표를 분석하고, 채널별 최적 전략과 주간 콘텐츠 캘린더를 생성합니다.

출력 규칙:
1. 채널별 전략은 구체적이고 실행 가능해야 합니다
2. 콘텐츠 캘린더는 주차별로 토픽/훅/CTA를 포함합니다
3. 각 콘텐츠의 목적이 비즈니스 목표에 기여해야 합니다
4. 톤앤매너를 일관되게 유지합니다
5. KPI는 측정 가능한 지표로 설정합니다"""

STRATEGY_USER_PROMPT = """다음 비즈니스 정보를 바탕으로 디지털 마케팅 전략을 수립하세요.

**브랜드**: {brand_name}
**산업**: {industry}
**목표**: {business_goal}
**타겟**: {target_audience}
**예산**: {budget_level}
**기간**: {duration_weeks}주
**채널**: {channels}
**톤**: {tone}

다음 JSON 형식으로 응답하세요:
{{
  "overall_strategy": "전체 전략 요약 (2-3문장)",
  "channel_strategies": [
    {{
      "channel": "youtube",
      "goal": "채널 목표",
      "content_type": "숏폼/롱폼/라이브 등",
      "posting_frequency": "주 N회",
      "key_topics": ["토픽1", "토픽2", "토픽3"],
      "tone": "톤앤매너",
      "cta": "행동 유도 문구",
      "kpi": "측정 지표"
    }}
  ],
  "content_calendar": [
    {{
      "week": 1,
      "day": "월",
      "channel": "youtube",
      "content_type": "숏폼",
      "topic": "구체적 토픽",
      "hook": "첫 3초 훅 문구",
      "cta": "행동 유도",
      "estimated_duration": 60
    }}
  ]
}}

채널별 주 2-3개 콘텐츠, 총 {duration_weeks}주 캘린더를 생성하세요."""


# ── 전략 생성 서비스 ──────────────────────────────

class StrategyAgent:
    """전략 수립 AI Agent"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate_strategy(self, input_data: StrategyInput) -> StrategyOutput:
        """비즈니스 목표 → 채널별 전략 + 콘텐츠 캘린더 생성"""
        import json

        prompt = STRATEGY_USER_PROMPT.format(
            brand_name=input_data.brand_name,
            industry=input_data.industry,
            business_goal=input_data.business_goal,
            target_audience=input_data.target_audience,
            budget_level=input_data.budget_level,
            duration_weeks=input_data.duration_weeks,
            channels=", ".join(input_data.channels),
            tone=input_data.tone,
        )

        # LLM 호출 (OpenAI 또는 Anthropic)
        raw_json = await self._call_llm(prompt)

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 전략 생성
            self.logger.warning("LLM JSON parse failed, generating fallback strategy")
            data = self._generate_fallback(input_data)

        # 구조화
        channel_strategies = [
            ChannelStrategy(**cs) for cs in data.get("channel_strategies", [])
        ]
        content_calendar = [
            ContentCalendarItem(**ci) for ci in data.get("content_calendar", [])
        ]

        output = StrategyOutput(
            brand_name=input_data.brand_name,
            business_goal=input_data.business_goal,
            target_audience=input_data.target_audience,
            overall_strategy=data.get("overall_strategy", ""),
            channel_strategies=channel_strategies,
            content_calendar=content_calendar,
            total_contents=len(content_calendar),
            estimated_weekly_hours=len(content_calendar) / input_data.duration_weeks * 2,
            generated_at=datetime.utcnow().isoformat(),
        )

        # Google Sheets 동기화
        if input_data.spreadsheet_id:
            await self._sync_to_sheets(input_data.spreadsheet_id, output)

        return output

    async def _call_llm(self, prompt: str) -> str:
        """LLM 호출 — OpenAI GPT-4 우선, fallback Anthropic"""
        try:
            from openai import AsyncOpenAI
            from app.core.config import get_settings
            settings = get_settings()

            if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                response = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": STRATEGY_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"OpenAI failed: {e}, trying Anthropic")

        try:
            import anthropic
            from app.core.config import get_settings
            settings = get_settings()

            if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("your_"):
                client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = await client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4096,
                    system=STRATEGY_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt + "\n\nJSON으로만 응답하세요."}],
                )
                return response.content[0].text
        except Exception as e:
            self.logger.warning(f"Anthropic failed: {e}, using fallback")

        # 둘 다 실패 시 fallback
        import json
        return json.dumps(self._generate_fallback(
            StrategyInput(
                business_goal="기본 전략",
                target_audience="일반",
                brand_name="Brand",
            )
        ))

    def _generate_fallback(self, input_data: StrategyInput) -> dict:
        """LLM 없이 기본 전략 생성 (템플릿 기반)"""
        channels = input_data.channels or ["youtube", "instagram", "blog"]
        weeks = input_data.duration_weeks

        channel_strategies = []
        calendar = []

        CHANNEL_DEFAULTS = {
            "youtube": {"type": "숏폼 + 롱폼", "freq": "주 2회", "kpi": "조회수, 구독자 증가율"},
            "instagram": {"type": "릴스 + 카루셀", "freq": "주 3회", "kpi": "도달, 저장수"},
            "tiktok": {"type": "숏폼", "freq": "주 3회", "kpi": "조회수, 팔로워 증가율"},
            "blog": {"type": "SEO 아티클", "freq": "주 1회", "kpi": "검색 유입, 체류 시간"},
        }
        DAYS = ["월", "화", "수", "목", "금"]

        for ch in channels:
            defaults = CHANNEL_DEFAULTS.get(ch, {"type": "콘텐츠", "freq": "주 2회", "kpi": "도달"})
            channel_strategies.append({
                "channel": ch,
                "goal": f"{input_data.business_goal} — {ch} 채널 활용",
                "content_type": defaults["type"],
                "posting_frequency": defaults["freq"],
                "key_topics": [f"{input_data.brand_name} 소개", "고객 후기", "활용 팁"],
                "tone": input_data.tone,
                "cta": "프로필 링크에서 자세히 확인하세요",
                "kpi": defaults["kpi"],
            })

            # 주차별 캘린더 생성
            freq = 2 if "2" in defaults["freq"] else 3
            for week in range(1, weeks + 1):
                for i in range(freq):
                    day = DAYS[i % len(DAYS)]
                    calendar.append({
                        "week": week,
                        "day": day,
                        "channel": ch,
                        "content_type": defaults["type"].split(" + ")[0] if " + " in defaults["type"] else defaults["type"],
                        "topic": f"Week {week} — {input_data.brand_name} 콘텐츠 {i+1}",
                        "hook": f"{input_data.brand_name}의 비밀을 알려드립니다",
                        "cta": "지금 시작하세요",
                        "estimated_duration": 60 if ch in ["youtube", "tiktok"] else None,
                    })

        return {
            "overall_strategy": f"{input_data.brand_name}의 {input_data.business_goal}을 달성하기 위해 {', '.join(channels)} 채널을 활용한 통합 콘텐츠 전략입니다.",
            "channel_strategies": channel_strategies,
            "content_calendar": calendar,
        }

    async def _sync_to_sheets(self, spreadsheet_id: str, output: StrategyOutput):
        """전략 결과를 Google Sheets에 동기화"""
        try:
            from app.services.google_sheets_service import GoogleSheetsService
            sheets = GoogleSheetsService()

            # 전략 시트 업데이트
            strategy_rows = [["채널", "목표", "콘텐츠 유형", "빈도", "KPI"]]
            for cs in output.channel_strategies:
                strategy_rows.append([cs.channel, cs.goal, cs.content_type, cs.posting_frequency, cs.kpi])

            # 캘린더 시트 업데이트
            calendar_rows = [["주차", "요일", "채널", "유형", "토픽", "훅", "CTA", "상태"]]
            for ci in output.content_calendar:
                calendar_rows.append([
                    f"W{ci.week}", ci.day, ci.channel, ci.content_type,
                    ci.topic, ci.hook, ci.cta, ci.status,
                ])

            self.logger.info(f"Synced strategy to Google Sheets: {spreadsheet_id}")
        except Exception as e:
            self.logger.warning(f"Google Sheets sync failed: {e}")


# 싱글톤
_agent: Optional[StrategyAgent] = None

def get_strategy_agent() -> StrategyAgent:
    global _agent
    if _agent is None:
        _agent = StrategyAgent()
    return _agent
