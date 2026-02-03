"""Zero-Fault Audio API 엔드포인트"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.tasks.audio_tasks import (
    generate_verified_audio_task,
    batch_generate_verified_audio_task,
    remove_silence_task,
    remove_fillers_task
)
from app.services.text_normalizer import get_text_normalizer

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
        logger.info(f"Starting audio generation for text: {request.text[:50]}...")

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

        # bytes 타입 데이터를 안전하게 처리하는 함수
        def sanitize_data(data):
            """bytes 타입 데이터를 필터링하여 JSON 직렬화 가능하게 처리"""
            if data is None:
                return None
            if isinstance(data, bytes):
                # bytes 데이터는 제외 (오디오 바이너리 등)
                return None
            if isinstance(data, dict):
                return {k: sanitize_data(v) for k, v in data.items()}
            if isinstance(data, (list, tuple)):
                return [sanitize_data(item) for item in data]
            if isinstance(data, (str, int, float, bool)):
                return data
            # 기타 객체는 문자열로 변환
            return str(data)

        response = {
            "task_id": task_id,
            "status": task_result.status,
            "info": sanitize_data(task_result.info)
        }

        # 완료된 경우 결과 포함
        if task_result.status == "SUCCESS":
            # info 안에 result가 있는지 확인
            task_info = task_result.info
            if task_info and isinstance(task_info, dict):
                result_data = task_info.get("result", {})
                if result_data:
                    response["result"] = {
                        "status": result_data.get("status"),
                        "audio_path": result_data.get("audio_path"),
                        "attempts": result_data.get("attempts"),
                        "final_similarity": result_data.get("final_similarity"),
                        "transcribed_text": result_data.get("transcribed_text"),
                        "original_text": result_data.get("original_text"),
                        "normalized_text": result_data.get("normalized_text"),
                        "normalization_mappings": result_data.get("normalization_mappings", {})
                    }
                else:
                    # task_result.result 직접 확인 (fallback)
                    result = sanitize_data(task_result.result)
                    if result:
                        response["result"] = {
                            "status": result.get("status"),
                            "audio_path": result.get("audio_path"),
                            "attempts": result.get("attempts"),
                            "final_similarity": result.get("final_similarity"),
                            "transcribed_text": result.get("transcribed_text"),
                            "original_text": result.get("original_text"),
                            "normalized_text": result.get("normalized_text"),
                            "normalization_mappings": result.get("normalization_mappings", {})
                        }

        # 실패한 경우 에러 정보
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.info)

        return response

    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
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
        logger.info(f"Starting batch audio generation for {len(request.texts)} texts")

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
    voices = tts.get_available_voices()

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


class NormalizeTextRequest(BaseModel):
    """텍스트 정규화 요청"""
    text: str = Field(..., min_length=1, max_length=10000, description="정규화할 텍스트")


class NormalizeTextResponse(BaseModel):
    """텍스트 정규화 응답"""
    original: str
    normalized: str
    mappings: dict


class RemoveSilenceRequest(BaseModel):
    """무음 제거 요청"""
    audio_url: str = Field(..., description="오디오 파일 URL (Cloudinary 또는 로컬)")
    threshold_db: int = Field(-40, ge=-80, le=-20, description="무음 기준 (dB, 기본값: -40dB)")
    min_silence_duration: float = Field(0.5, ge=0.1, le=5.0, description="최소 무음 길이 (초, 기본값: 0.5초)")


class RemoveSilenceResponse(BaseModel):
    """무음 제거 응답"""
    success: bool
    task_id: str
    message: str
    original_audio_url: str


class RemoveFillersRequest(BaseModel):
    """필러 워드 제거 요청"""
    audio_url: str = Field(..., description="오디오 파일 URL (Cloudinary 또는 로컬)")
    filler_words: list[str] = Field(
        default=["음", "어", "그", "저", "아"],
        description="제거할 필러 워드 목록"
    )
    language: str = Field("ko", description="언어 코드 (ko, en 등)")


class RemoveFillersResponse(BaseModel):
    """필러 워드 제거 응답"""
    success: bool
    task_id: str
    message: str
    original_audio_url: str


@router.post("/normalize-text", response_model=NormalizeTextResponse)
async def normalize_text(request: NormalizeTextRequest):
    """
    한국어 텍스트 정규화 (숫자 → 한글)

    **변환 규칙**:
    - 연도: 2024년 → 이천이십사년
    - 날짜: 1월 15일 → 일월 십오일
    - 금액: 2,000원 → 이천원
    - 개수: 3개 → 세개
    - 나이: 25살 → 스물다섯살
    - 시간: 2시 30분 → 두시 삼십분
    - 전화번호: 010-1234-5678 → 공일공 일이삼사 오육칠팔
    - 퍼센트: 95.5% → 구십오점오퍼센트

    **사용 목적**:
    TTS 생성 전에 숫자를 한글로 변환하여 TTS/STT 일관성 보장

    **예시**:
    ```json
    {
        "text": "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
    }
    ```

    **응답**:
    ```json
    {
        "original": "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다.",
        "normalized": "이천이십사년 일월 십오일, 사과 세개를 이천원에 샀습니다.",
        "mappings": {
            "2024년": "이천이십사년",
            "1월": "일월",
            "15일": "십오일",
            "3개": "세개",
            "2,000원": "이천원"
        }
    }
    ```
    """
    try:
        normalizer = get_text_normalizer()
        normalized, mappings = normalizer.normalize_script(request.text)

        return NormalizeTextResponse(
            original=request.text,
            normalized=normalized,
            mappings=mappings
        )

    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.post("/remove-silence", response_model=RemoveSilenceResponse)
async def remove_silence(request: RemoveSilenceRequest):
    """
    무음 구간 자동 제거

    **워크플로우**:
    1. 오디오 파일 다운로드
    2. FFmpeg silencedetect로 무음 구간 감지
    3. FFmpeg silenceremove로 무음 제거
    4. 처리된 파일 Cloudinary 업로드
    5. 결과 반환

    **사용 사례**:
    - 녹음 후 불필요한 무음 구간 제거
    - 편집 시간 단축
    - Vrew 스타일 자동 편집

    **예시**:
    ```json
    {
        "audio_url": "https://cloudinary.com/sample.mp3",
        "threshold_db": -40,
        "min_silence_duration": 0.5
    }
    ```

    **응답**:
    - task_id로 /audio/status/{task_id} 조회
    - 완료 시 processed_audio_url 반환
    """
    try:
        logger.info(f"Starting silence removal for: {request.audio_url}")

        # Celery 작업 실행
        task = remove_silence_task.delay(
            audio_url=request.audio_url,
            threshold_db=request.threshold_db,
            min_silence_duration=request.min_silence_duration
        )

        return RemoveSilenceResponse(
            success=True,
            task_id=task.id,
            message=f"무음 제거 작업 시작. /audio/status/{task.id}로 진행 상황 확인하세요.",
            original_audio_url=request.audio_url
        )

    except Exception as e:
        logger.error(f"Silence removal request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-fillers", response_model=RemoveFillersResponse)
async def remove_fillers(request: RemoveFillersRequest):
    """
    필러 워드 자동 제거

    **워크플로우**:
    1. 오디오 파일 다운로드
    2. OpenAI Whisper STT로 word-level transcription
    3. 필러 워드 감지 (음, 어, 그, 저 등)
    4. FFmpeg로 해당 구간 제거
    5. 처리된 파일 Cloudinary 업로드
    6. 결과 반환

    **사용 사례**:
    - 팟캐스트 편집
    - 프레젠테이션 음성 개선
    - Vrew 스타일 자동 편집

    **예시**:
    ```json
    {
        "audio_url": "https://cloudinary.com/sample.mp3",
        "filler_words": ["음", "어", "그", "저", "아"],
        "language": "ko"
    }
    ```

    **응답**:
    - task_id로 /audio/status/{task_id} 조회
    - 완료 시 processed_audio_url, transcript, removed_words 반환
    """
    try:
        logger.info(f"Starting filler removal for: {request.audio_url}")

        # Celery 작업 실행
        task = remove_fillers_task.delay(
            audio_url=request.audio_url,
            filler_words=request.filler_words,
            language=request.language
        )

        return RemoveFillersResponse(
            success=True,
            task_id=task.id,
            message=f"필러 워드 제거 작업 시작. /audio/status/{task.id}로 진행 상황 확인하세요.",
            original_audio_url=request.audio_url
        )

    except Exception as e:
        logger.error(f"Filler removal request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
