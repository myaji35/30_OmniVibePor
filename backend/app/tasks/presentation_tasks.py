"""Celery 프리젠테이션 영상 생성 작업 (최적화)"""
import logging
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import nullcontext

from app.tasks.celery_app import celery_app
from app.services.presentation_video_generator import get_video_generator
from app.services.neo4j_client import get_neo4j_client
from app.models.presentation import PresentationStatus

# Conditional imports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Redis client for result caching
_redis_cache = None


def get_redis_cache():
    """Get Redis cache client"""
    global _redis_cache
    if _redis_cache is None and REDIS_AVAILABLE:
        from app.core.config import get_settings
        settings = get_settings()
        try:
            _redis_cache = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,  # Use separate DB for task results
                decode_responses=True,
                socket_timeout=5
            )
            _redis_cache.ping()
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            _redis_cache = None
    return _redis_cache


@celery_app.task(
    name="generate_presentation_video",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=3600,  # 1 hour timeout
    soft_time_limit=3300,  # 55 minutes soft timeout
    priority=5,  # Normal priority (0-9, higher is more priority)
    track_started=True,  # Track task start time
    acks_late=True,  # Acknowledge task after completion (prevents loss)
    reject_on_worker_lost=True  # Reject if worker crashes
)
def generate_presentation_video_task(
    self,
    presentation_id: str,
    slides: List[Dict[str, Any]],
    audio_path: str,
    output_filename: str,
    transition_effect: str = "fade",
    transition_duration: float = 0.5,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.3,
    user_id: Optional[str] = None,
    priority: int = 5  # Task priority override
) -> Dict:
    """
    프리젠테이션 영상 생성 Celery 작업

    Args:
        presentation_id: 프리젠테이션 ID
        slides: 슬라이드 정보 리스트
            [{"image_path": "...", "start_time": 0, "end_time": 5.5, "duration": 5.5}, ...]
        audio_path: 나레이션 오디오 파일 경로
        output_filename: 출력 파일명
        transition_effect: 전환 효과 (fade/slide/zoom/none)
        transition_duration: 전환 시간 (초)
        bgm_path: 배경음악 파일 경로 (옵션)
        bgm_volume: 배경음악 볼륨 (0.0~1.0)
        user_id: 사용자 ID

    Returns:
        {
            "status": "success" | "failed",
            "presentation_id": str,
            "video_path": str,
            "duration": float,
            "task_id": str,
            "error": str (실패 시)
        }
    """
    logger.info(
        f"Starting presentation video generation task - "
        f"presentation_id: {presentation_id}, "
        f"slides: {len(slides)}, "
        f"transition: {transition_effect}, "
        f"user: {user_id or 'anonymous'}, "
        f"task_id: {self.request.id}"
    )

    # Check cache for identical request (deduplication)
    cache_key = _generate_task_cache_key(presentation_id, slides, transition_effect)
    cached_result = _get_cached_task_result(cache_key)
    if cached_result:
        logger.info(f"Task result cache hit: {presentation_id}")
        return cached_result

    try:
        # Neo4j 상태 업데이트 (VIDEO_RENDERING)
        _update_presentation_status(
            presentation_id=presentation_id,
            status=PresentationStatus.VIDEO_RENDERING
        )

        # 영상 생성 서비스 실행
        video_generator = get_video_generator()

        # 비동기 함수를 동기 방식으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        video_path = loop.run_until_complete(
            video_generator.generate_video(
                slides=slides,
                audio_path=audio_path,
                output_filename=output_filename,
                transition_effect=transition_effect,
                transition_duration=transition_duration,
                bgm_path=bgm_path,
                bgm_volume=bgm_volume
            )
        )

        loop.close()

        # 영상 길이 계산
        total_duration = sum(slide["duration"] for slide in slides)

        # Neo4j 업데이트 (VIDEO_READY)
        _update_presentation_status(
            presentation_id=presentation_id,
            status=PresentationStatus.VIDEO_READY,
            video_path=video_path
        )

        logger.info(
            f"Presentation video generation completed - "
            f"presentation_id: {presentation_id}, "
            f"video_path: {video_path}, "
            f"duration: {total_duration:.1f}s"
        )

        result = {
            "status": "success",
            "presentation_id": presentation_id,
            "video_path": video_path,
            "duration": total_duration,
            "task_id": self.request.id
        }

        # Cache successful result (1 hour TTL)
        _cache_task_result(cache_key, result, ttl=3600)

        return result

    except Exception as e:
        logger.error(
            f"Presentation video generation failed - "
            f"presentation_id: {presentation_id}, "
            f"error: {str(e)}"
        )

        # Neo4j 상태 업데이트 (FAILED)
        _update_presentation_status(
            presentation_id=presentation_id,
            status=PresentationStatus.FAILED,
            error=str(e)
        )

        # 재시도
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying presentation video generation (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)

        return {
            "status": "failed",
            "presentation_id": presentation_id,
            "error": str(e),
            "task_id": self.request.id
        }


def _update_presentation_status(
    presentation_id: str,
    status: PresentationStatus,
    video_path: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """
    Neo4j 프리젠테이션 상태 업데이트

    Args:
        presentation_id: 프리젠테이션 ID
        status: 상태
        video_path: 영상 경로 (옵션)
        error: 에러 메시지 (옵션)
    """
    try:
        neo4j_client = get_neo4j_client()

        update_data = {
            "status": status.value,
            "updated_at": "datetime()"
        }

        if video_path:
            update_data["video_path"] = video_path

        if error:
            update_data["error"] = error

        query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        SET p += $update_data
        RETURN p
        """

        neo4j_client.execute_query(
            query=query,
            parameters={
                "presentation_id": presentation_id,
                "update_data": update_data
            }
        )

        logger.info(f"Updated presentation status: {presentation_id} -> {status.value}")

    except Exception as e:
        logger.error(f"Failed to update presentation status: {e}")
        # 상태 업데이트 실패는 치명적이지 않으므로 로그만 남김


def _generate_task_cache_key(
    presentation_id: str,
    slides: List[Dict[str, Any]],
    transition_effect: str
) -> str:
    """Generate cache key for task deduplication"""
    # Create deterministic hash from task parameters
    key_data = {
        "presentation_id": presentation_id,
        "slides": slides,
        "transition": transition_effect
    }
    key_string = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"task_result:{key_hash}"


def _get_cached_task_result(cache_key: str) -> Optional[Dict]:
    """Retrieve cached task result"""
    redis_client = get_redis_cache()
    if not redis_client:
        return None

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Cache retrieval error: {e}")

    return None


def _cache_task_result(cache_key: str, result: Dict, ttl: int) -> None:
    """Cache task result"""
    redis_client = get_redis_cache()
    if not redis_client:
        return

    try:
        redis_client.setex(cache_key, ttl, json.dumps(result))
        logger.debug(f"Cached task result: {cache_key}")
    except Exception as e:
        logger.error(f"Cache storage error: {e}")


@celery_app.task(
    name="cleanup_temp_files",
    priority=1,  # Low priority cleanup task
    time_limit=300  # 5 minutes timeout
)
def cleanup_temp_files_task(file_paths: List[str]) -> Dict:
    """
    임시 파일 정리 작업

    Args:
        file_paths: 삭제할 파일 경로 리스트

    Returns:
        정리 결과
    """
    logger.info(f"Cleaning up {len(file_paths)} temp files")

    deleted = []
    failed = []

    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                deleted.append(file_path)
                logger.debug(f"Deleted temp file: {file_path}")
            else:
                logger.warning(f"Temp file not found: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete temp file {file_path}: {e}")
            failed.append({"path": file_path, "error": str(e)})

    return {
        "deleted": len(deleted),
        "failed": len(failed),
        "deleted_files": deleted,
        "failed_files": failed
    }
