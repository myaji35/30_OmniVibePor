"""Celery 영상 작업 (립싱크, 편집 등)"""
import logging
import asyncio
from typing import Optional, Dict

from app.tasks.celery_app import celery_app
from app.services.lipsync_service import get_lipsync_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_lipsync",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def generate_lipsync_task(
    self,
    video_path: str,
    audio_path: str,
    output_path: str,
    method: str = "auto",
    user_id: Optional[str] = None
) -> Dict:
    """
    립싱크 영상 생성 Celery 작업

    Args:
        video_path: 입력 영상 경로
        audio_path: 입력 오디오 경로
        output_path: 출력 영상 경로
        method: 사용할 방법 ("auto", "heygen", "wav2lip")
        user_id: 사용자 ID

    Returns:
        {
            "status": "success" | "failed",
            "output_path": str,
            "method_used": "heygen" | "wav2lip",
            "duration": float,
            "cost_usd": float,
            "task_id": str
        }
    """
    logger.info(
        f"Starting lipsync task - "
        f"video: {video_path}, audio: {audio_path}, "
        f"method: {method}, user: {user_id or 'anonymous'}, "
        f"task_id: {self.request.id}"
    )

    try:
        # LipsyncService 실행
        lipsync_service = get_lipsync_service()
        result = asyncio.run(
            lipsync_service.generate_lipsync(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path,
                method=method
            )
        )

        # Celery 작업 정보 추가
        result["task_id"] = self.request.id
        result["user_id"] = user_id

        # 성공 로깅
        method_used = result.get("method_used", "unknown")
        duration = result.get("duration", 0)
        cost = result.get("cost_usd", 0)

        logger.info(
            f"Lipsync task completed - "
            f"method: {method_used}, duration: {duration:.1f}s, "
            f"cost: ${cost:.3f}, user: {user_id}"
        )

        return result

    except Exception as e:
        logger.error(f"Lipsync task failed: {e}")

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying lipsync task... "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # 최종 실패
        return {
            "status": "error",
            "error": str(e),
            "task_id": self.request.id,
            "user_id": user_id
        }


@celery_app.task(name="batch_generate_lipsync")
def batch_generate_lipsync_task(
    video_audio_pairs: list[tuple[str, str]],
    output_paths: list[str],
    method: str = "auto",
    user_id: Optional[str] = None
) -> Dict:
    """
    여러 립싱크 영상 배치 생성 Celery 작업

    Args:
        video_audio_pairs: [(video_path, audio_path), ...]
        output_paths: [output_path, ...]
        method: 사용할 방법
        user_id: 사용자 ID

    Returns:
        {
            "status": "completed" | "error",
            "results": [...],
            "summary": {
                "total": int,
                "success": int,
                "failed": int,
                "total_duration": float,
                "total_cost_usd": float
            }
        }
    """
    logger.info(
        f"Starting batch lipsync task - "
        f"total: {len(video_audio_pairs)}, method: {method}, "
        f"user: {user_id or 'anonymous'}"
    )

    if len(video_audio_pairs) != len(output_paths):
        return {
            "status": "error",
            "error": "video_audio_pairs and output_paths length mismatch"
        }

    try:
        lipsync_service = get_lipsync_service()
        results = []

        # 각 쌍 순차 처리
        for (video_path, audio_path), output_path in zip(video_audio_pairs, output_paths):
            try:
                result = asyncio.run(
                    lipsync_service.generate_lipsync(
                        video_path=video_path,
                        audio_path=audio_path,
                        output_path=output_path,
                        method=method
                    )
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Batch item failed: {e}")
                results.append({
                    "status": "error",
                    "error": str(e),
                    "video_path": video_path,
                    "audio_path": audio_path
                })

        # 통계 계산
        summary = {
            "total": len(results),
            "success": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") != "success"),
            "total_duration": sum(r.get("duration", 0) for r in results),
            "total_cost_usd": sum(r.get("cost_usd", 0) for r in results)
        }

        logger.info(
            f"Batch lipsync completed - "
            f"success: {summary['success']}/{summary['total']}, "
            f"cost: ${summary['total_cost_usd']:.2f}"
        )

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Batch lipsync task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id
        }


@celery_app.task(name="check_lipsync_quality")
def check_lipsync_quality_task(
    video_path: str,
    user_id: Optional[str] = None
) -> Dict:
    """
    립싱크 품질 평가 Celery 작업

    Args:
        video_path: 평가할 영상 경로
        user_id: 사용자 ID

    Returns:
        {
            "status": "success" | "error",
            "video_path": str,
            "quality_scores": {
                "sync_score": float,
                "audio_quality": float,
                "video_quality": float
            }
        }
    """
    logger.info(f"Starting quality check task - video: {video_path}, user: {user_id}")

    try:
        lipsync_service = get_lipsync_service()
        quality_scores = asyncio.run(
            lipsync_service.check_lipsync_quality(video_path)
        )

        logger.info(
            f"Quality check completed - "
            f"sync: {quality_scores['sync_score']:.2f}, "
            f"audio: {quality_scores['audio_quality']:.2f}, "
            f"video: {quality_scores['video_quality']:.2f}"
        )

        return {
            "status": "success",
            "video_path": video_path,
            "quality_scores": quality_scores,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Quality check task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "video_path": video_path,
            "user_id": user_id
        }
