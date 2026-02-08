"""Celery 영상 작업 (립싱크, 편집, Remotion 렌더링 등)"""
import logging
import asyncio
from typing import Optional, Dict, Any, List

from app.tasks.celery_app import celery_app
from app.services.lipsync_service import get_lipsync_service
from app.services.remotion_service import get_remotion_service

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


# ==================== Remotion 렌더링 작업 ====================

@celery_app.task(
    name="render_video_with_remotion",
    bind=True,
    max_retries=2,
    default_retry_delay=120
)
def render_video_with_remotion_task(
    self,
    content_id: int,
    storyboard_blocks: List[Dict[str, Any]],
    campaign_concept: Dict[str, str],
    audio_url: Optional[str] = None,
    composition_id: str = "OmniVibeComposition"
) -> Dict[str, Any]:
    """
    Remotion 기반 영상 렌더링 Celery 작업

    Args:
        content_id: 콘텐츠 ID
        storyboard_blocks: Director Agent가 생성한 콘티 블록 리스트
        campaign_concept: 캠페인 컨셉 (gender, tone, style, platform)
        audio_url: Zero-Fault Audio Director 출력 URL
        composition_id: Remotion composition ID

    Returns:
        {
            "status": "success" | "failed",
            "content_id": int,
            "local_path": str,
            "cloudinary_url": str,
            "duration": int,
            "platform": str,
            "resolution": str,
            "task_id": str
        }
    """
    logger.info(
        f"🎬 Starting Remotion render task - "
        f"content_id: {content_id}, platform: {campaign_concept.get('platform', 'YouTube')}, "
        f"blocks: {len(storyboard_blocks)}, task_id: {self.request.id}"
    )

    try:
        remotion_service = get_remotion_service()

        # 1. Storyboard Blocks → Remotion Props 변환
        props = remotion_service.convert_storyboard_to_props(
            storyboard_blocks=storyboard_blocks,
            campaign_concept=campaign_concept,
            audio_url=audio_url
        )

        logger.info(f"✅ Props converted: {props['metadata']['sceneCount']} scenes, {props['metadata']['totalDuration']}s")

        # 2. Remotion 렌더링 (비동기)
        result = asyncio.run(
            remotion_service.render_video_with_remotion(
                content_id=content_id,
                props=props,
                composition_id=composition_id
            )
        )

        # Celery 작업 정보 추가
        result["task_id"] = self.request.id
        result["content_id"] = content_id

        logger.info(
            f"✅ Remotion render completed - "
            f"content_id: {content_id}, duration: {result['duration']}s, "
            f"url: {result['cloudinary_url']}"
        )

        return result

    except Exception as e:
        logger.error(f"❌ Remotion render task failed: {e}")

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying Remotion render task... "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # 최종 실패
        return {
            "status": "failed",
            "error": str(e),
            "content_id": content_id,
            "task_id": self.request.id
        }


@celery_app.task(name="validate_remotion_setup")
def validate_remotion_setup_task() -> Dict[str, Any]:
    """
    Remotion CLI 설치 및 설정 검증 작업

    Returns:
        {
            "status": "ok" | "error",
            "installed": bool,
            "version": str,
            "frontend_path": str,
            "compositions": List[Dict]
        }
    """
    logger.info("🔍 Validating Remotion setup...")

    try:
        remotion_service = get_remotion_service()

        # 1. Remotion CLI 설치 확인
        install_status = asyncio.run(
            remotion_service.validate_remotion_installation()
        )

        if not install_status.get("installed"):
            return {
                "status": "error",
                "error": "Remotion CLI not installed",
                "details": install_status
            }

        # 2. 사용 가능한 Composition 조회
        compositions = remotion_service.get_available_compositions()

        logger.info(
            f"✅ Remotion setup validated - "
            f"version: {install_status['version']}, "
            f"compositions: {len(compositions)}"
        )

        return {
            "status": "ok",
            "installed": True,
            "version": install_status["version"],
            "frontend_path": install_status["frontend_path"],
            "compositions": compositions
        }

    except Exception as e:
        logger.error(f"❌ Remotion setup validation failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="batch_render_videos")
def batch_render_videos_task(
    render_requests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    여러 영상 배치 렌더링 작업

    Args:
        render_requests: 렌더링 요청 리스트
            [
                {
                    "content_id": int,
                    "storyboard_blocks": List[Dict],
                    "campaign_concept": Dict,
                    "audio_url": str
                },
                ...
            ]

    Returns:
        {
            "status": "completed" | "error",
            "results": [...],
            "summary": {
                "total": int,
                "success": int,
                "failed": int,
                "total_duration": int
            }
        }
    """
    logger.info(f"🎬 Starting batch render task - total: {len(render_requests)}")

    try:
        remotion_service = get_remotion_service()
        results = []

        # 각 요청 순차 처리
        for request in render_requests:
            try:
                content_id = request["content_id"]
                props = remotion_service.convert_storyboard_to_props(
                    storyboard_blocks=request["storyboard_blocks"],
                    campaign_concept=request["campaign_concept"],
                    audio_url=request.get("audio_url")
                )

                result = asyncio.run(
                    remotion_service.render_video_with_remotion(
                        content_id=content_id,
                        props=props
                    )
                )
                results.append(result)

            except Exception as e:
                logger.error(f"❌ Batch item failed (content_id: {request.get('content_id')}): {e}")
                results.append({
                    "status": "failed",
                    "error": str(e),
                    "content_id": request.get("content_id")
                })

        # 통계 계산
        summary = {
            "total": len(results),
            "success": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") != "success"),
            "total_duration": sum(r.get("duration", 0) for r in results)
        }

        logger.info(
            f"✅ Batch render completed - "
            f"success: {summary['success']}/{summary['total']}, "
            f"total_duration: {summary['total_duration']}s"
        )

        return {
            "status": "completed",
            "results": results,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"❌ Batch render task failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
