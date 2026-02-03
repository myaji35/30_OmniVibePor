"""Writer 에이전트 API 엔드포인트"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging

# ⚠️ Lazy import: transformers UTF-8 문제 방지
# from app.services.writer_agent import get_writer_agent
from app.services.duration_calculator import (
    get_duration_calculator,
    calculate_duration,
    estimate_word_count,
    Language
)
from app.services.duration_learning_system import get_learning_system

router = APIRouter(prefix="/writer", tags=["Writer Agent"])
logger = logging.getLogger(__name__)


class ScriptGenerationRequest(BaseModel):
    """스크립트 생성 요청"""
    spreadsheet_id: str
    campaign_name: str
    topic: str
    platform: str = "YouTube"  # YouTube, Instagram, TikTok


class ScriptGenerationResponse(BaseModel):
    """스크립트 생성 응답"""
    success: bool
    campaign_name: Optional[str] = None
    topic: Optional[str] = None
    platform: Optional[str] = None
    script: Optional[str] = None
    hook: Optional[str] = None
    cta: Optional[str] = None
    estimated_duration: Optional[int] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=ScriptGenerationResponse)
async def generate_script(request: ScriptGenerationRequest):
    """
    스크립트 자동 생성

    LangGraph 기반 Writer 에이전트가:
    1. 구글 시트에서 전략 로드
    2. Neo4j에서 과거 스크립트 검색
    3. Claude (Anthropic)로 고품질 스크립트 초안 생성
    4. 플랫폼별 최적화
    5. Neo4j에 저장

    Args:
        spreadsheet_id: 구글 시트 ID
        campaign_name: 캠페인명
        topic: 소제목
        platform: 플랫폼 (YouTube, Instagram, TikTok)

    Returns:
        생성된 스크립트 및 메타데이터
    """
    # Lazy import to avoid transformers UTF-8 error on startup
    from app.services.writer_agent import get_writer_agent

    writer_agent = get_writer_agent()

    try:
        result = await writer_agent.generate_script(
            spreadsheet_id=request.spreadsheet_id,
            campaign_name=request.campaign_name,
            topic=request.topic,
            platform=request.platform
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "스크립트 생성에 실패했습니다")
            )

        return ScriptGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"스크립트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def check_health():
    """
    Writer 에이전트 상태 확인
    """
    try:
        # Lazy import to avoid transformers UTF-8 error on startup
        from app.services.writer_agent import get_writer_agent
        writer_agent = get_writer_agent()
        return {
            "status": "healthy",
            "message": "Writer agent is ready",
            "llm_model": "claude-3-haiku-20240307"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }


# ==================== Duration Calculator 엔드포인트 ====================

class DurationCalculateRequest(BaseModel):
    """시간 계산 요청"""
    text: str
    language: str = "ko"  # ko, en, ja, zh


class DurationCalculateResponse(BaseModel):
    """시간 계산 응답"""
    duration: float  # 예상 시간 (초)
    base_duration: float  # 기본 읽기 시간
    pause_duration: float  # 구두점 휴지 시간
    word_count: int  # 글자/단어 수
    correction_factor: float  # 보정 계수


class WordCountEstimateRequest(BaseModel):
    """글자 수 예측 요청"""
    target_duration: float  # 목표 시간 (초)
    language: str = "ko"
    margin: float = 0.1  # 오차 범위 (기본 10%)


class WordCountEstimateResponse(BaseModel):
    """글자 수 예측 응답"""
    min_words: int
    max_words: int
    target_words: int


@router.post("/calculate-duration", response_model=DurationCalculateResponse)
async def calculate_script_duration(request: DurationCalculateRequest):
    """
    텍스트 → 예상 오디오 시간 계산

    Args:
        text: 입력 텍스트
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        예상 시간, 글자 수, 휴지 시간 등

    Example:
        POST /api/v1/writer/calculate-duration
        {
            "text": "안녕하세요. 오늘은 좋은 날씨입니다.",
            "language": "ko"
        }

        Response:
        {
            "duration": 6.5,
            "base_duration": 6.0,
            "pause_duration": 0.5,
            "word_count": 20,
            "correction_factor": 1.0
        }
    """
    try:
        lang = Language(request.language)
        calculator = get_duration_calculator(lang)
        result = calculator.calculate(request.text)

        return DurationCalculateResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 언어입니다: {request.language}"
        )
    except Exception as e:
        logger.error(f"Duration calculation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"시간 계산 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/estimate-word-count", response_model=WordCountEstimateResponse)
async def estimate_required_word_count(request: WordCountEstimateRequest):
    """
    목표 시간 → 필요 글자/단어 수 예측

    Args:
        target_duration: 목표 시간 (초)
        language: 언어 코드
        margin: 오차 범위 (기본 10%)

    Returns:
        최소/최대/목표 글자 수

    Example:
        POST /api/v1/writer/estimate-word-count
        {
            "target_duration": 60,
            "language": "ko",
            "margin": 0.1
        }

        Response:
        {
            "min_words": 180,
            "max_words": 220,
            "target_words": 200
        }
    """
    try:
        lang = Language(request.language)
        calculator = get_duration_calculator(lang)
        result = calculator.estimate_for_target_duration(
            target_duration=request.target_duration,
            margin=request.margin
        )

        return WordCountEstimateResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 언어입니다: {request.language}"
        )
    except Exception as e:
        logger.error(f"Word count estimation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"글자 수 예측 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/update-correction-factor")
async def update_duration_correction_factor(
    language: str,
    predicted: float,
    actual: float
):
    """
    실제 TTS 시간 기반 보정 계수 업데이트

    Args:
        language: 언어 코드
        predicted: 예측한 시간 (초)
        actual: 실제 TTS 시간 (초)

    Returns:
        업데이트된 보정 계수

    Example:
        POST /api/v1/writer/update-correction-factor?language=ko&predicted=60&actual=58

        Response:
        {
            "success": true,
            "language": "ko",
            "old_factor": 1.0,
            "new_factor": 0.97,
            "message": "보정 계수가 업데이트되었습니다"
        }
    """
    try:
        lang = Language(language)
        calculator = get_duration_calculator(lang)

        old_factor = calculator.correction_factor
        calculator.update_correction_factor(predicted, actual)
        new_factor = calculator.correction_factor

        return {
            "success": True,
            "language": language,
            "old_factor": round(old_factor, 3),
            "new_factor": round(new_factor, 3),
            "message": "보정 계수가 업데이트되었습니다"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 언어입니다: {language}"
        )
    except Exception as e:
        logger.error(f"Correction factor update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"보정 계수 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


# ==================== Duration Learning System 엔드포인트 ====================

class LearningRecordRequest(BaseModel):
    """학습 레코드 기록 요청"""
    text: str
    language: str = "ko"
    actual_duration: float
    platform: Optional[str] = None
    voice_id: Optional[str] = None


class LearningRecordResponse(BaseModel):
    """학습 레코드 기록 응답"""
    success: bool
    text: str
    language: str
    predicted_duration: float
    actual_duration: float
    accuracy: float
    correction_factor: float
    platform: Optional[str] = None
    voice_id: Optional[str] = None


@router.post("/learning/record", response_model=LearningRecordResponse)
async def record_learning_data(request: LearningRecordRequest):
    """
    실제 TTS 결과 기록 및 자동 학습

    TTS 생성 후 실제 오디오 시간을 기록하면:
    1. 예측 시간과 실제 시간 비교
    2. 정확도 계산
    3. 보정 계수 자동 업데이트
    4. Neo4j에 학습 데이터 저장

    Args:
        text: 원본 텍스트
        language: 언어 코드
        actual_duration: 실제 TTS 시간 (초)
        platform: 플랫폼 (선택)
        voice_id: 음성 ID (선택)

    Returns:
        학습 레코드 및 정확도 정보

    Example:
        POST /api/v1/writer/learning/record
        {
            "text": "안녕하세요. 오늘은 좋은 날씨입니다.",
            "language": "ko",
            "actual_duration": 6.8,
            "platform": "YouTube",
            "voice_id": "voice_123"
        }

        Response:
        {
            "success": true,
            "text": "안녕하세요. 오늘은 좋은 날씨입니다.",
            "language": "ko",
            "predicted_duration": 6.5,
            "actual_duration": 6.8,
            "accuracy": 95.4,
            "correction_factor": 1.046,
            "platform": "YouTube",
            "voice_id": "voice_123"
        }
    """
    try:
        learning_system = get_learning_system()

        record = learning_system.record_prediction(
            text=request.text,
            language=request.language,
            actual_duration=request.actual_duration,
            platform=request.platform,
            voice_id=request.voice_id
        )

        return LearningRecordResponse(
            success=True,
            text=record.text,
            language=record.language,
            predicted_duration=record.predicted_duration,
            actual_duration=record.actual_duration,
            accuracy=record.accuracy,
            correction_factor=record.correction_factor,
            platform=record.platform,
            voice_id=record.voice_id
        )

    except Exception as e:
        logger.error(f"Learning record failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"학습 데이터 기록 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/learning/stats")
async def get_learning_statistics(
    language: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100
):
    """
    학습 통계 조회

    Args:
        language: 언어 필터 (선택)
        platform: 플랫폼 필터 (선택)
        limit: 최대 레코드 수 (기본: 100)

    Returns:
        총 레코드 수, 평균 정확도, 보정 계수 등

    Example:
        GET /api/v1/writer/learning/stats?language=ko&limit=50

        Response:
        {
            "total_records": 47,
            "avg_accuracy": 94.5,
            "avg_correction_factor": 1.023,
            "min_accuracy": 87.2,
            "max_accuracy": 99.1,
            "recent_records": [...]
        }
    """
    try:
        learning_system = get_learning_system()
        stats = learning_system.get_learning_stats(
            language=language,
            platform=platform,
            limit=limit
        )

        return stats

    except Exception as e:
        logger.error(f"Get learning stats failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"학습 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/learning/accuracy-by-language")
async def get_accuracy_by_language():
    """
    언어별 정확도 조회

    Returns:
        언어별 레코드 수, 평균 정확도, 평균 보정 계수

    Example:
        GET /api/v1/writer/learning/accuracy-by-language

        Response:
        [
            {
                "language": "ko",
                "total": 150,
                "avg_accuracy": 94.5,
                "avg_factor": 1.023
            },
            {
                "language": "en",
                "total": 80,
                "avg_accuracy": 92.3,
                "avg_factor": 1.045
            }
        ]
    """
    try:
        learning_system = get_learning_system()
        results = learning_system.get_accuracy_by_language()

        return results

    except Exception as e:
        logger.error(f"Get accuracy by language failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"언어별 정확도 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/learning/trend")
async def get_accuracy_trend(
    language: str,
    days: int = 7
):
    """
    시간별 정확도 트렌드 조회

    Args:
        language: 언어 코드
        days: 조회 기간 (일, 기본: 7)

    Returns:
        시간별 정확도 및 보정 계수 변화

    Example:
        GET /api/v1/writer/learning/trend?language=ko&days=7

        Response:
        [
            {
                "timestamp": "2026-02-01T10:30:00",
                "accuracy": 94.5,
                "correction_factor": 1.023,
                "predicted": 60.0,
                "actual": 61.4
            },
            ...
        ]
    """
    try:
        learning_system = get_learning_system()
        trend = learning_system.get_accuracy_trend(
            language=language,
            days=days
        )

        return trend

    except Exception as e:
        logger.error(f"Get accuracy trend failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"정확도 트렌드 조회 중 오류가 발생했습니다: {str(e)}"
        )
