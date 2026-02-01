"""Zero-Fault Audio API 엔드포인트"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.tasks.audio_tasks import generate_verified_audio_task, batch_generate_verified_audio_task

router = APIRouter()
logger = logging.getLogger(__name__)


class AudioGenerateRequest(BaseModel):
    """오디오 생성 요청"""
    text: str = Field(..., min_length=1, max_length=5000, description="변환할 텍스트 (최대 5000자)")
    voice_id: Optional[str] = Field(None, description="음성 ID (기본값: rachel)")
    language: str = Field("ko", description="언어 코드 (ko, en 등)")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    accuracy_threshold: float = Field(0.95, ge=0.0, le=1.0, description="정확도 임계값")
    max_attempts: int = Field(5, ge=1, le=10, description="최대 재시도 횟수")


class BatchAudioGenerateRequest(BaseModel):
    """배치 오디오 생성 요청"""
    texts: list[str] = Field(..., min_items=1, max_items=100, description="텍스트 리스트")
    voice_id: Optional[str] = None
    language: str = "ko"
    user_id: Optional[str] = None


@router.post("/generate")
async def generate_audio(request: AudioGenerateRequest):
    """
    Zero-Fault Audio 생성

    **워크플로우**:
    1. ElevenLabs TTS로 오디오 생성
    2. OpenAI Whisper STT로 검증
    3. 원본과 비교 (유사도 계산)
    4. 정확도 95% 미만이면 재생성 (최대 5회)
    5. 검증된 오디오 반환

    **비동기 처리**: Celery 작업 큐 사용
    """
    try:
        with logger.span("api.generate_audio"):
            # Celery 작업 실행
            task = generate_verified_audio_task.delay(
                text=request.text,
                voice_id=request.voice_id,
                language=request.language,
                user_id=request.user_id,
                accuracy_threshold=request.accuracy_threshold,
                max_attempts=request.max_attempts
            )

            return {
                "status": "processing",
                "task_id": task.id,
                "message": "Zero-Fault Audio 생성 시작. /audio/status/{task_id}로 진행 상황 확인하세요.",
                "text_preview": request.text[:100]
            }

    except Exception as e:
        logger.error(f"Audio generation request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Celery 작업 상태 조회

    **상태**:
    - PENDING: 대기 중
    - STARTED: 실행 중
    - SUCCESS: 완료
    - FAILURE: 실패
    - RETRY: 재시도 중
    """
    try:
        from app.tasks.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task_result.status,
            "info": task_result.info
        }

        # 완료된 경우 결과 포함
        if task_result.status == "SUCCESS":
            result = task_result.result
            response["result"] = {
                "status": result.get("status"),
                "audio_path": result.get("audio_path"),
                "attempts": result.get("attempts"),
                "final_similarity": result.get("final_similarity"),
                "transcribed_text": result.get("transcribed_text")
            }

        # 실패한 경우 에러 정보
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.info)

        return response

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{task_id}")
async def download_audio(task_id: str):
    """
    생성된 오디오 파일 다운로드

    **사용법**:
    1. /audio/generate로 작업 시작
    2. /audio/status/{task_id}로 완료 확인
    3. /audio/download/{task_id}로 파일 다운로드
    """
    try:
        from app.tasks.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        if task_result.status != "SUCCESS":
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed yet. Status: {task_result.status}"
            )

        result = task_result.result
        audio_path = result.get("audio_path")

        if not audio_path:
            raise HTTPException(
                status_code=404,
                detail="Audio file not found"
            )

        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=f"verified_audio_{task_id[:8]}.mp3"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate")
async def batch_generate_audio(request: BatchAudioGenerateRequest):
    """
    여러 텍스트 배치 처리

    **사용 사례**:
    - 시리즈 영상의 여러 스크립트 한번에 처리
    - 챕터별 오디오 생성

    **제한**:
    - 최대 100개 텍스트
    """
    try:
        with logger.span("api.batch_generate_audio"):
            task = batch_generate_verified_audio_task.delay(
                texts=request.texts,
                voice_id=request.voice_id,
                language=request.language,
                user_id=request.user_id
            )

            return {
                "status": "processing",
                "task_id": task.id,
                "total_texts": len(request.texts),
                "message": "배치 처리 시작. /audio/status/{task_id}로 확인하세요."
            }

    except Exception as e:
        logger.error(f"Batch generation request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices():
    """
    사용 가능한 음성 목록

    **ElevenLabs 기본 음성**:
    - rachel: 여성, 미국 영어
    - domi: 여성, 미국 영어
    - bella: 여성, 미국 영어
    - antoni: 남성, 미국 영어
    - josh: 남성, 미국 영어
    """
    from app.services.tts_service import get_tts_service

    tts = get_tts_service()
    voices = tts.list_available_voices()

    return {
        "voices": voices,
        "total": len(voices)
    }


@router.get("/usage")
async def get_usage_info():
    """
    ElevenLabs API 사용량 조회

    **정보**:
    - 총 생성 문자 수
    - 예상 비용
    """
    from app.services.tts_service import get_tts_service

    tts = get_tts_service()
    usage = tts.get_usage_info()

    return usage
