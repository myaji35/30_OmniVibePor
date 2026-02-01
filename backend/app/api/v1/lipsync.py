"""Lipsync API 엔드포인트"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import uuid
import logging

from app.tasks.video_tasks import generate_lipsync_task, check_lipsync_quality_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lipsync", tags=["lipsync"])


# ==================== Pydantic 모델 ====================

class LipsyncCreateResponse(BaseModel):
    """립싱크 생성 응답"""
    job_id: str
    task_id: str
    status: str
    message: str


class LipsyncStatusResponse(BaseModel):
    """립싱크 상태 응답"""
    status: str  # "processing", "completed", "failed"
    job_id: str
    task_id: str
    result: Optional[dict] = None
    error: Optional[str] = None


class QualityCheckResponse(BaseModel):
    """품질 평가 응답"""
    status: str
    quality_scores: dict


# ==================== 엔드포인트 ====================

@router.post("/create", response_model=LipsyncCreateResponse)
async def create_lipsync(
    video: UploadFile = File(..., description="입력 영상 파일 (MP4, MOV, AVI)"),
    audio: UploadFile = File(..., description="입력 오디오 파일 (MP3, WAV, M4A)"),
    method: str = Form("auto", description="사용할 방법 (auto, heygen, wav2lip)"),
    user_id: Optional[str] = Form(None, description="사용자 ID")
):
    """
    립싱크 영상 생성 요청

    ## Parameters
    - **video**: 입력 영상 파일
    - **audio**: 입력 오디오 파일
    - **method**: 사용할 립싱크 방법
      - `auto`: HeyGen 우선 → Wav2Lip Fallback (기본)
      - `heygen`: HeyGen API만 사용
      - `wav2lip`: Wav2Lip만 사용
    - **user_id**: 사용자 ID (선택)

    ## Returns
    - **job_id**: 작업 고유 ID
    - **task_id**: Celery 작업 ID
    - **status**: 작업 상태 ("processing")

    ## Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/lipsync/create" \\
      -F "video=@input.mp4" \\
      -F "audio=@audio.mp3" \\
      -F "method=auto"
    ```
    """
    logger.info(
        f"Received lipsync request - "
        f"video: {video.filename}, audio: {audio.filename}, "
        f"method: {method}, user: {user_id or 'anonymous'}"
    )

    # 방법 검증
    if method not in ["auto", "heygen", "wav2lip"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid method: {method}. Use 'auto', 'heygen', or 'wav2lip'"
        )

    # 파일 확장자 검증
    video_ext = Path(video.filename).suffix.lower()
    audio_ext = Path(audio.filename).suffix.lower()

    allowed_video = [".mp4", ".mov", ".avi", ".mkv"]
    allowed_audio = [".mp3", ".wav", ".m4a", ".aac"]

    if video_ext not in allowed_video:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video format: {video_ext}. Allowed: {allowed_video}"
        )

    if audio_ext not in allowed_audio:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format: {audio_ext}. Allowed: {allowed_audio}"
        )

    # 고유 ID 생성
    job_id = str(uuid.uuid4())

    # 파일 저장 경로
    upload_dir = Path("./uploads/lipsync")
    upload_dir.mkdir(parents=True, exist_ok=True)

    output_dir = Path("./outputs/lipsync")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = upload_dir / f"{job_id}_video{video_ext}"
    audio_path = upload_dir / f"{job_id}_audio{audio_ext}"
    output_path = output_dir / f"{job_id}_synced.mp4"

    # 파일 저장
    try:
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
            logger.info(f"Video saved: {video_path} ({len(content)} bytes)")

        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
            logger.info(f"Audio saved: {audio_path} ({len(content)} bytes)")

    except Exception as e:
        logger.error(f"File save failed: {e}")
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    # Celery 작업 큐에 추가
    try:
        task = generate_lipsync_task.delay(
            video_path=str(video_path),
            audio_path=str(audio_path),
            output_path=str(output_path),
            method=method,
            user_id=user_id
        )

        logger.info(f"Lipsync task queued - job_id: {job_id}, task_id: {task.id}")

        return LipsyncCreateResponse(
            job_id=job_id,
            task_id=task.id,
            status="processing",
            message="Lipsync generation started"
        )

    except Exception as e:
        logger.error(f"Task queue failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task queue failed: {str(e)}")


@router.get("/status/{task_id}", response_model=LipsyncStatusResponse)
async def get_lipsync_status(task_id: str):
    """
    립싱크 작업 상태 조회

    ## Parameters
    - **task_id**: Celery 작업 ID

    ## Returns
    - **status**: 작업 상태
      - `processing`: 처리 중
      - `completed`: 완료
      - `failed`: 실패
    - **result**: 작업 결과 (완료 시)
    - **error**: 에러 메시지 (실패 시)

    ## Example
    ```bash
    curl "http://localhost:8000/api/v1/lipsync/status/{task_id}"
    ```
    """
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    logger.info(f"Checking lipsync status - task_id: {task_id}")

    task = AsyncResult(task_id, app=celery_app)

    if task.ready():
        result = task.result

        # 성공
        if isinstance(result, dict) and result.get("status") == "success":
            return LipsyncStatusResponse(
                status="completed",
                job_id=result.get("task_id", "unknown"),
                task_id=task_id,
                result=result
            )
        # 실패
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            return LipsyncStatusResponse(
                status="failed",
                job_id="unknown",
                task_id=task_id,
                error=error_msg
            )
    else:
        # 처리 중
        return LipsyncStatusResponse(
            status="processing",
            job_id="unknown",
            task_id=task_id
        )


@router.get("/download/{job_id}")
async def download_lipsync_video(job_id: str):
    """
    완성된 립싱크 영상 다운로드

    ## Parameters
    - **job_id**: 작업 고유 ID

    ## Returns
    파일 다운로드

    ## Example
    ```bash
    curl -O "http://localhost:8000/api/v1/lipsync/download/{job_id}"
    ```
    """
    output_path = Path(f"./outputs/lipsync/{job_id}_synced.mp4")

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Lipsync video not found: {job_id}"
        )

    logger.info(f"Downloading lipsync video - job_id: {job_id}")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"lipsync_{job_id}.mp4"
    )


@router.post("/quality-check/{job_id}", response_model=QualityCheckResponse)
async def check_lipsync_quality(job_id: str):
    """
    립싱크 품질 평가

    ## Parameters
    - **job_id**: 작업 고유 ID

    ## Returns
    - **quality_scores**: 품질 점수
      - `sync_score`: 립싱크 정확도 (0-1)
      - `audio_quality`: 오디오 품질 (0-1)
      - `video_quality`: 영상 품질 (0-1)

    ## Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/lipsync/quality-check/{job_id}"
    ```
    """
    video_path = Path(f"./outputs/lipsync/{job_id}_synced.mp4")

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Lipsync video not found: {job_id}"
        )

    logger.info(f"Checking lipsync quality - job_id: {job_id}")

    # Celery 작업 실행
    task = check_lipsync_quality_task.delay(str(video_path))
    result = task.get(timeout=60)

    if result.get("status") == "success":
        return QualityCheckResponse(
            status="success",
            quality_scores=result["quality_scores"]
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Quality check failed: {result.get('error')}"
        )


@router.delete("/{job_id}")
async def delete_lipsync_job(job_id: str):
    """
    립싱크 작업 및 관련 파일 삭제

    ## Parameters
    - **job_id**: 작업 고유 ID

    ## Returns
    삭제 결과

    ## Example
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/lipsync/{job_id}"
    ```
    """
    logger.info(f"Deleting lipsync job - job_id: {job_id}")

    deleted_files = []

    # 관련 파일 삭제
    patterns = [
        f"./uploads/lipsync/{job_id}_video.*",
        f"./uploads/lipsync/{job_id}_audio.*",
        f"./outputs/lipsync/{job_id}_synced.mp4"
    ]

    import glob
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                Path(file_path).unlink()
                deleted_files.append(file_path)
                logger.info(f"Deleted: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

    if not deleted_files:
        raise HTTPException(
            status_code=404,
            detail=f"No files found for job_id: {job_id}"
        )

    return {
        "status": "success",
        "message": f"Deleted {len(deleted_files)} files",
        "deleted_files": deleted_files
    }


@router.get("/list")
async def list_lipsync_jobs(limit: int = 50):
    """
    립싱크 작업 목록 조회

    ## Parameters
    - **limit**: 최대 결과 수 (기본: 50)

    ## Returns
    작업 목록

    ## Example
    ```bash
    curl "http://localhost:8000/api/v1/lipsync/list?limit=10"
    ```
    """
    output_dir = Path("./outputs/lipsync")

    if not output_dir.exists():
        return {"jobs": []}

    # 모든 synced.mp4 파일 찾기
    import glob
    files = glob.glob(str(output_dir / "*_synced.mp4"))

    jobs = []
    for file_path in sorted(files, key=lambda x: Path(x).stat().st_mtime, reverse=True)[:limit]:
        file_path = Path(file_path)
        job_id = file_path.stem.replace("_synced", "")

        jobs.append({
            "job_id": job_id,
            "filename": file_path.name,
            "size_mb": file_path.stat().st_size / (1024 * 1024),
            "created_at": file_path.stat().st_ctime
        })

    return {"jobs": jobs, "total": len(jobs)}
