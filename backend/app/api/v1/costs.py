"""비용 추적 API 엔드포인트

모든 외부 API 호출의 비용을 조회하고 분석하는 엔드포인트를 제공합니다.

주요 기능:
- 총 비용 조회 (필터링 가능)
- 일별 비용 트렌드 (차트용)
- 제공자별 비용 분석
- 프로젝트별 비용 조회
- 프로젝트 비용 예상
- CSV 내보내기
- 대시보드 데이터
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
import csv
from io import StringIO

from app.services.cost_tracker import (
    get_cost_tracker,
    APIProvider,
    APIService,
    CostTracker
)

router = APIRouter(prefix="/costs")


# ==================== Request/Response Models ====================

class CostQueryRequest(BaseModel):
    """비용 조회 요청"""
    user_id: Optional[str] = Field(None, description="사용자 ID로 필터링")
    project_id: Optional[str] = Field(None, description="프로젝트 ID로 필터링")
    provider: Optional[str] = Field(None, description="API 제공자로 필터링 (예: openai, elevenlabs)")
    start_date: Optional[datetime] = Field(None, description="시작 날짜 (ISO 8601 형식)")
    end_date: Optional[datetime] = Field(None, description="종료 날짜 (ISO 8601 형식)")


class EstimateCostRequest(BaseModel):
    """프로젝트 비용 예상 요청"""
    script_length: int = Field(..., description="스크립트 글자 수", ge=1)
    video_duration: int = Field(..., description="영상 길이 (초)", ge=1)
    platform: str = Field(default="YouTube", description="플랫폼 (YouTube, Instagram, TikTok)")

    class Config:
        json_schema_extra = {
            "example": {
                "script_length": 500,
                "video_duration": 60,
                "platform": "YouTube"
            }
        }


class CostTotalResponse(BaseModel):
    """총 비용 응답"""
    total_cost: float = Field(..., description="총 비용 (USD)")
    record_count: int = Field(..., description="비용 기록 개수")
    by_provider: Dict[str, float] = Field(..., description="제공자별 비용 분석")
    query_params: Dict[str, Any] = Field(..., description="쿼리 파라미터")

    class Config:
        json_schema_extra = {
            "example": {
                "total_cost": 15.42,
                "record_count": 128,
                "by_provider": {
                    "openai": 5.32,
                    "elevenlabs": 8.10,
                    "google_veo": 2.00
                },
                "query_params": {
                    "user_id": "user_abc123",
                    "start_date": "2026-01-01T00:00:00",
                    "end_date": "2026-02-02T23:59:59"
                }
            }
        }


class DailyCostTrend(BaseModel):
    """일별 비용 트렌드"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    total_cost: float = Field(..., description="해당 날짜의 총 비용 (USD)")
    by_provider: Dict[str, float] = Field(..., description="제공자별 비용")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-01",
                "total_cost": 3.25,
                "by_provider": {
                    "openai": 1.15,
                    "elevenlabs": 2.10
                }
            }
        }


class ProjectCostEstimate(BaseModel):
    """프로젝트 비용 예상"""
    writer_agent: float = Field(..., description="작가 에이전트 비용 (Claude)")
    tts: float = Field(..., description="TTS 비용 (ElevenLabs)")
    stt: float = Field(..., description="STT 비용 (Whisper)")
    character: float = Field(..., description="캐릭터 생성 비용 (Nano Banana)")
    video_generation: float = Field(..., description="영상 생성 비용 (Google Veo)")
    lipsync: float = Field(..., description="립싱크 비용 (HeyGen)")
    total: float = Field(..., description="총 예상 비용 (USD)")

    class Config:
        json_schema_extra = {
            "example": {
                "writer_agent": 0.12,
                "tts": 0.15,
                "stt": 0.01,
                "character": 0.05,
                "video_generation": 6.00,
                "lipsync": 3.00,
                "total": 9.33
            }
        }


class DashboardData(BaseModel):
    """대시보드 데이터"""
    total_cost_today: float = Field(..., description="오늘 총 비용")
    total_cost_week: float = Field(..., description="이번 주 총 비용")
    total_cost_month: float = Field(..., description="이번 달 총 비용")
    daily_trend: List[DailyCostTrend] = Field(..., description="최근 7일 일별 트렌드")
    by_provider: Dict[str, float] = Field(..., description="제공자별 비용 (이번 달)")
    top_projects: List[Dict[str, Any]] = Field(..., description="비용이 가장 많이 든 프로젝트 Top 5")


# ==================== API Endpoints ====================

@router.get("/total", response_model=CostTotalResponse, summary="총 비용 조회")
async def get_total_cost(
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링"),
    provider: Optional[str] = Query(None, description="API 제공자로 필터링 (예: openai, elevenlabs)"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (ISO 8601 형식, 예: 2026-01-01T00:00:00)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (ISO 8601 형식, 예: 2026-02-02T23:59:59)")
):
    """
    필터 조건에 따라 총 비용을 조회합니다.

    **필터 옵션**:
    - `user_id`: 특정 사용자의 비용만 조회
    - `project_id`: 특정 프로젝트의 비용만 조회
    - `provider`: 특정 API 제공자의 비용만 조회
    - `start_date`, `end_date`: 기간으로 필터링

    **반환값**:
    - 총 비용 (USD)
    - 비용 기록 개수
    - 제공자별 비용 분석
    """
    tracker = get_cost_tracker()

    # 날짜 파싱
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format. Use ISO 8601 format (e.g., 2026-01-01T00:00:00)"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format. Use ISO 8601 format (e.g., 2026-02-02T23:59:59)"
            )

    # Provider 검증
    provider_enum = None
    if provider:
        try:
            provider_enum = APIProvider(provider)
        except ValueError:
            valid_providers = [p.value for p in APIProvider]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Valid options: {valid_providers}"
            )

    # 비용 조회
    result = tracker.get_total_cost(
        user_id=user_id,
        project_id=project_id,
        provider=provider_enum,
        start_date=start_dt,
        end_date=end_dt
    )

    # 쿼리 파라미터 정보 추가
    query_params = {}
    if user_id:
        query_params["user_id"] = user_id
    if project_id:
        query_params["project_id"] = project_id
    if provider:
        query_params["provider"] = provider
    if start_date:
        query_params["start_date"] = start_date
    if end_date:
        query_params["end_date"] = end_date

    return CostTotalResponse(
        total_cost=result.get("total_cost", 0.0),
        record_count=result.get("record_count", 0),
        by_provider=result.get("by_provider", {}),
        query_params=query_params
    )


@router.get("/trend", response_model=List[DailyCostTrend], summary="일별 비용 트렌드")
async def get_cost_trend(
    days: int = Query(default=7, ge=1, le=90, description="조회할 일수 (1-90일)"),
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링")
):
    """
    일별 비용 트렌드를 조회합니다 (차트용).

    **파라미터**:
    - `days`: 조회할 일수 (기본: 7일, 최대: 90일)
    - `user_id`: 특정 사용자의 트렌드만 조회
    - `project_id`: 특정 프로젝트의 트렌드만 조회

    **반환값**:
    - 날짜별 총 비용 및 제공자별 비용 분석
    - 최신 날짜부터 내림차순 정렬
    """
    tracker = get_cost_tracker()

    trend_data = tracker.get_daily_cost_trend(
        days=days,
        user_id=user_id,
        project_id=project_id
    )

    return [
        DailyCostTrend(
            date=item["date"],
            total_cost=item["total_cost"],
            by_provider=item["by_provider"]
        )
        for item in trend_data
    ]


@router.get("/by-provider", summary="제공자별 비용 분석")
async def get_cost_by_provider(
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링"),
    days: int = Query(default=30, ge=1, le=365, description="조회할 일수 (1-365일)")
):
    """
    API 제공자별 비용을 분석합니다.

    **파라미터**:
    - `days`: 조회할 일수 (기본: 30일)
    - `user_id`: 특정 사용자의 비용만 조회
    - `project_id`: 특정 프로젝트의 비용만 조회

    **반환값**:
    - 제공자별 총 비용 및 비율
    - 비용이 높은 순으로 정렬
    """
    tracker = get_cost_tracker()

    # 기간 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    result = tracker.get_total_cost(
        user_id=user_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )

    total_cost = result.get("total_cost", 0.0)
    by_provider = result.get("by_provider", {})

    # 제공자별 비율 계산
    provider_analysis = []
    for provider, cost in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
        percentage = (cost / total_cost * 100) if total_cost > 0 else 0.0
        provider_analysis.append({
            "provider": provider,
            "cost": cost,
            "percentage": round(percentage, 2)
        })

    return {
        "total_cost": total_cost,
        "period_days": days,
        "providers": provider_analysis
    }


@router.get("/by-project/{project_id}", summary="프로젝트별 비용 조회")
async def get_cost_by_project(
    project_id: str,
    start_date: Optional[str] = Query(None, description="시작 날짜 (ISO 8601 형식)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (ISO 8601 형식)")
):
    """
    특정 프로젝트의 총 비용을 조회합니다.

    **파라미터**:
    - `project_id`: 프로젝트 ID (경로 파라미터)
    - `start_date`, `end_date`: 기간으로 필터링 (선택)

    **반환값**:
    - 프로젝트 총 비용
    - 제공자별 비용 분석
    - 단계별 비용 분석 (TTS, STT, 영상 생성 등)
    """
    tracker = get_cost_tracker()

    # 날짜 파싱
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_date format. Use ISO 8601 format"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid end_date format. Use ISO 8601 format"
            )

    # 비용 조회
    result = tracker.get_total_cost(
        project_id=project_id,
        start_date=start_dt,
        end_date=end_dt
    )

    # 서비스별 비용 분석 (by_provider를 by_service로 변환)
    # 실제로는 Neo4j에서 service별로도 그룹화해야 하지만, 현재는 provider로만 제공

    return {
        "project_id": project_id,
        "total_cost": result.get("total_cost", 0.0),
        "record_count": result.get("record_count", 0),
        "by_provider": result.get("by_provider", {}),
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.post("/estimate", response_model=ProjectCostEstimate, summary="프로젝트 비용 예상")
async def estimate_project_cost(request: EstimateCostRequest):
    """
    새 프로젝트의 예상 비용을 계산합니다.

    **요청 본문**:
    - `script_length`: 스크립트 글자 수
    - `video_duration`: 영상 길이 (초)
    - `platform`: 플랫폼 (YouTube, Instagram, TikTok)

    **반환값**:
    - 각 단계별 예상 비용 (Writer, TTS, STT, 캐릭터, 영상, 립싱크)
    - 총 예상 비용 (USD)

    **예시**:
    - 500자 스크립트, 60초 영상 → 약 $9.33
    """
    tracker = get_cost_tracker()

    estimates = tracker.estimate_project_cost(
        script_length=request.script_length,
        video_duration=request.video_duration,
        platform=request.platform
    )

    return ProjectCostEstimate(
        writer_agent=estimates.get("writer_agent", 0.0),
        tts=estimates.get("tts", 0.0),
        stt=estimates.get("stt", 0.0),
        character=estimates.get("character", 0.0),
        video_generation=estimates.get("video_generation", 0.0),
        lipsync=estimates.get("lipsync", 0.0),
        total=estimates.get("total", 0.0)
    )


@router.get("/export", summary="비용 데이터 CSV 내보내기")
async def export_costs_csv(
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링"),
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링"),
    provider: Optional[str] = Query(None, description="API 제공자로 필터링"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (ISO 8601 형식)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (ISO 8601 형식)")
):
    """
    필터 조건에 따라 비용 데이터를 CSV 파일로 내보냅니다.

    **필터 옵션**:
    - `user_id`, `project_id`, `provider`: 필터링
    - `start_date`, `end_date`: 기간 필터링

    **반환값**:
    - CSV 파일 (다운로드)
    - 헤더: Date, Provider, Service, Cost (USD), User ID, Project ID
    """
    tracker = get_cost_tracker()

    # 날짜 파싱
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Provider 검증
    provider_enum = None
    if provider:
        try:
            provider_enum = APIProvider(provider)
        except ValueError:
            valid_providers = [p.value for p in APIProvider]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Valid options: {valid_providers}"
            )

    # 트렌드 데이터로부터 CSV 생성 (실제로는 개별 레코드를 조회해야 하지만, 현재는 일별 집계 사용)
    # TODO: Neo4j에 개별 레코드 조회 메서드 추가 필요

    # 임시로 일별 트렌드 데이터를 CSV로 변환
    trend_data = tracker.get_daily_cost_trend(
        days=90,  # 최대 90일
        user_id=user_id,
        project_id=project_id
    )

    # CSV 생성
    output = StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow(["Date", "Total Cost (USD)", "Provider Breakdown"])

    # 데이터
    for item in trend_data:
        date = item["date"]
        total_cost = item["total_cost"]
        provider_breakdown = ", ".join([f"{k}: ${v:.4f}" for k, v in item["by_provider"].items()])
        writer.writerow([date, f"${total_cost:.4f}", provider_breakdown])

    # CSV 파일 반환
    csv_content = output.getvalue()
    output.close()

    filename = f"omnivibe_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/dashboard", response_model=DashboardData, summary="대시보드 데이터")
async def get_dashboard_data(
    user_id: Optional[str] = Query(None, description="사용자 ID로 필터링")
):
    """
    대시보드에 표시할 종합 비용 데이터를 조회합니다.

    **포함 데이터**:
    - 오늘, 이번 주, 이번 달 총 비용
    - 최근 7일 일별 트렌드 (차트용)
    - 이번 달 제공자별 비용 분석
    - 비용이 가장 많이 든 프로젝트 Top 5

    **반환값**:
    - 모든 대시보드 데이터를 포함한 종합 응답
    """
    tracker = get_cost_tracker()

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # 오늘 비용
    today_result = tracker.get_total_cost(
        user_id=user_id,
        start_date=today_start,
        end_date=now
    )

    # 이번 주 비용
    week_result = tracker.get_total_cost(
        user_id=user_id,
        start_date=week_start,
        end_date=now
    )

    # 이번 달 비용
    month_result = tracker.get_total_cost(
        user_id=user_id,
        start_date=month_start,
        end_date=now
    )

    # 최근 7일 트렌드
    trend_data = tracker.get_daily_cost_trend(
        days=7,
        user_id=user_id
    )

    daily_trend = [
        DailyCostTrend(
            date=item["date"],
            total_cost=item["total_cost"],
            by_provider=item["by_provider"]
        )
        for item in trend_data
    ]

    # Top 프로젝트 (현재는 구현 불가 - Neo4j에 project별 집계 쿼리 필요)
    # TODO: Neo4j에 프로젝트별 비용 집계 메서드 추가
    top_projects = []

    return DashboardData(
        total_cost_today=today_result.get("total_cost", 0.0),
        total_cost_week=week_result.get("total_cost", 0.0),
        total_cost_month=month_result.get("total_cost", 0.0),
        daily_trend=daily_trend,
        by_provider=month_result.get("by_provider", {}),
        top_projects=top_projects
    )
