"""Director 에이전트 API 엔드포인트"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
import logging
from pathlib import Path

from app.services.audio_director_agent import get_director_agent as get_audio_director_agent
from app.services.director_agent import get_video_director_agent
from app.tasks.director_tasks import (
    generate_video_from_script_task,
    estimate_video_cost_task,
    get_project_cost_report_task
)

router = APIRouter(prefix="/director", tags=["Director Agent"])
logger = logging.getLogger(__name__)


class AudioGenerationRequest(BaseModel):
    """오디오 생성 요청"""
    script: str
    campaign_name: str
    topic: str
    voice_id: Optional[str] = None
    language: str = "ko"
    accuracy_threshold: float = 0.95
    max_attempts: int = 5


class AudioGenerationResponse(BaseModel):
    """오디오 생성 응답"""
    success: bool
    campaign_name: Optional[str] = None
    topic: Optional[str] = None
    audio_file_path: Optional[str] = None
    script: Optional[str] = None
    transcription: Optional[str] = None
    similarity_score: Optional[float] = None
    attempts: Optional[int] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate-audio", response_model=AudioGenerationResponse)
async def generate_audio(request: AudioGenerationRequest):
    """
    오디오 생성 및 검증 (Zero-Fault Loop)

    LangGraph 기반 Director 에이전트가:
    1. TTS 생성 (ElevenLabs)
    2. STT 검증 (OpenAI Whisper)
    3. 유사도 계산
    4. 95% 이상 정확도 달성까지 반복 (최대 5회)
    5. Neo4j에 저장

    Args:
        script: 스크립트 텍스트
        campaign_name: 캠페인명
        topic: 소제목
        voice_id: 커스텀 음성 ID (옵션)
        language: 언어 코드 (기본값: "ko")
        accuracy_threshold: 정확도 임계값 (기본값: 0.95)
        max_attempts: 최대 시도 횟수 (기본값: 5)

    Returns:
        생성된 오디오 정보 및 검증 결과
    """
    director_agent = get_audio_director_agent()

    try:
        result = await director_agent.generate_audio(
            script=request.script,
            campaign_name=request.campaign_name,
            topic=request.topic,
            voice_id=request.voice_id,
            language=request.language,
            accuracy_threshold=request.accuracy_threshold,
            max_attempts=request.max_attempts
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "오디오 생성에 실패했습니다")
            )

        return AudioGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"오디오 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/download-audio/{filename}")
async def download_audio(filename: str):
    """
    생성된 오디오 파일 다운로드

    Args:
        filename: 오디오 파일명

    Returns:
        오디오 파일
    """
    try:
        audio_dir = Path("./generated_audio")
        file_path = audio_dir / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"오디오 파일을 찾을 수 없습니다: {filename}"
            )

        return FileResponse(
            path=str(file_path),
            media_type="audio/mpeg",
            filename=filename
        )

    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"오디오 다운로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def check_health():
    """
    Director 에이전트 상태 확인
    """
    try:
        audio_director_agent = get_audio_director_agent()
        video_director_agent = get_video_director_agent()
        return {
            "status": "healthy",
            "message": "Director agents are ready",
            "audio_director": {
                "tts_service": "OpenAI TTS",
                "stt_service": "OpenAI Whisper",
                "zero_fault_loop": "enabled",
                "available_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "video_director": {
                "character_service": "Nano Banana",
                "video_generation": "Google Veo",
                "lipsync": "HeyGen/Wav2Lip",
                "subtitle_generation": "OpenAI Whisper"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }


# ==================== 영상 생성 API ====================


class VideoGenerationRequest(BaseModel):
    """영상 생성 요청"""
    project_id: str
    script: str
    audio_path: str
    persona_id: Optional[str] = None
    gender: str = "female"
    age_range: str = "30-40"
    character_style: str = "professional"
    async_mode: bool = True  # True: Celery 작업, False: 동기 실행


class VideoGenerationResponse(BaseModel):
    """영상 생성 응답"""
    success: bool
    project_id: str
    task_id: Optional[str] = None  # Celery 작업 ID (async_mode=True 시)
    final_video_path: Optional[str] = None
    subtitle_srt_path: Optional[str] = None
    character_id: Optional[str] = None
    total_duration: Optional[float] = None
    total_cost_usd: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate-video", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    스크립트와 오디오로 완성된 영상 생성

    LangGraph 기반 Video Director 에이전트가:
    1. 캐릭터 로드/생성 (Nano Banana)
    2. 영상 클립 생성 (Google Veo)
    3. 립싱크 적용 (HeyGen/Wav2Lip)
    4. 자막 생성 (Whisper Timestamps)
    5. 최종 렌더링 (FFmpeg)
    6. Neo4j에 메타데이터 저장

    Args:
        project_id: 프로젝트 ID
        script: 스크립트 텍스트
        audio_path: 오디오 파일 경로
        persona_id: 페르소나 ID (옵션)
        gender: 성별 (male, female, neutral)
        age_range: 연령대 (20-30, 30-40, 40-50, 50-60)
        character_style: 캐릭터 스타일 (professional, casual, creative, formal)
        async_mode: 비동기 실행 여부 (True: Celery, False: 동기)

    Returns:
        생성된 영상 정보 또는 Celery 작업 ID
    """
    try:
        if request.async_mode:
            # Celery 비동기 실행 (권장)
            task = generate_video_from_script_task.apply_async(
                kwargs={
                    "project_id": request.project_id,
                    "script": request.script,
                    "audio_path": request.audio_path,
                    "persona_id": request.persona_id,
                    "gender": request.gender,
                    "age_range": request.age_range,
                    "character_style": request.character_style
                }
            )

            logger.info(
                f"Video generation task submitted: "
                f"project={request.project_id}, task_id={task.id}"
            )

            return VideoGenerationResponse(
                success=True,
                project_id=request.project_id,
                task_id=task.id
            )

        else:
            # 동기 실행 (테스트용)
            logger.warning(
                f"Synchronous video generation requested for project: {request.project_id}. "
                f"This may take a long time. Consider using async_mode=True."
            )

            director = get_video_director_agent()
            result = await director.generate_video(
                project_id=request.project_id,
                script=request.script,
                audio_path=request.audio_path,
                persona_id=request.persona_id,
                gender=request.gender,
                age_range=request.age_range,
                character_style=request.character_style
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "영상 생성에 실패했습니다")
                )

            return VideoGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"영상 생성 중 오류가 발생했습니다: {str(e)}"
        )


class CostEstimateRequest(BaseModel):
    """비용 예상 요청"""
    script_length: int
    video_duration: int
    platform: str = "YouTube"


@router.post("/estimate-cost")
async def estimate_cost(request: CostEstimateRequest):
    """
    영상 생성 예상 비용 계산

    Args:
        script_length: 스크립트 글자 수
        video_duration: 예상 영상 길이 (초)
        platform: 플랫폼 (YouTube, Instagram, TikTok 등)

    Returns:
        {
            "total_cost_usd": float,
            "breakdown": {...}
        }
    """
    try:
        task = estimate_video_cost_task.apply_async(
            kwargs={
                "script_length": request.script_length,
                "video_duration": request.video_duration,
                "platform": request.platform
            }
        )

        # 비용 예상은 빠르므로 동기적으로 결과 대기
        result = task.get(timeout=10)

        return result

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"비용 예상 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/cost-report/{project_id}")
async def get_cost_report(project_id: str):
    """
    프로젝트 비용 리포트 조회

    Args:
        project_id: 프로젝트 ID

    Returns:
        {
            "total_cost_usd": float,
            "by_provider": {...},
            "record_count": int
        }
    """
    try:
        task = get_project_cost_report_task.apply_async(
            kwargs={"project_id": project_id}
        )

        result = task.get(timeout=10)

        return result

    except Exception as e:
        logger.error(f"Cost report retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"비용 리포트 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/download-video/{project_id}/{filename}")
async def download_video(project_id: str, filename: str):
    """
    생성된 영상 파일 다운로드

    Args:
        project_id: 프로젝트 ID
        filename: 영상 파일명

    Returns:
        영상 파일
    """
    try:
        video_dir = Path("./outputs/videos")
        file_path = video_dir / filename

        # 보안: project_id가 파일명에 포함되어 있는지 확인
        if not filename.startswith(project_id):
            raise HTTPException(
                status_code=403,
                detail="접근 권한이 없습니다"
            )

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"영상 파일을 찾을 수 없습니다: {filename}"
            )

        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"영상 다운로드 중 오류가 발생했습니다: {str(e)}"
        )
