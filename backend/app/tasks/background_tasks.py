"""
배경 이미지 생성 Celery 작업
비동기 배경 생성 및 블록 업데이트
"""
import logging
from typing import Optional
from celery import Task
from app.tasks.celery_app import celery_app
from app.services.background_selector import BackgroundSelector
from app.services.image_generation import ImageGenerationService
from app.tasks.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_background_image", bind=True, max_retries=3)
def generate_background_task(
    self: Task,
    block_id: int,
    prompt: str,
    style: str = "natural",
    size: str = "1024x1024"
) -> dict:
    """
    DALL-E 배경 이미지 생성 (비동기)

    Args:
        block_id: 스토리보드 블록 ID
        prompt: DALL-E 프롬프트
        style: natural | vivid
        size: 1024x1024 | 1792x1024 | 1024x1792

    Returns:
        {
            "success": True,
            "block_id": 1,
            "background_url": "https://...",
            "metadata": {...}
        }
    """
    try:
        logger.info(f"[Task] 배경 생성 시작 - Block ID: {block_id}")

        # 진행률 추적
        tracker = ProgressTracker()
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Generating background image",
            progress=0.1
        )

        # DALL-E 이미지 생성
        service = ImageGenerationService()

        # Celery 작업은 동기 함수이므로 asyncio 사용
        import asyncio
        result = asyncio.run(
            service.generate_background_image(
                prompt=prompt,
                style=style,
                size=size
            )
        )

        # 진행률 업데이트
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Image generated, updating database",
            progress=0.8
        )

        # TODO: SQLite에 업데이트
        # from app.lib.db import update_storyboard_block
        # update_storyboard_block(block_id, {
        #     "background_url": result['image_url'],
        #     "background_type": "ai_generated",
        #     "background_metadata": result['metadata']
        # })

        logger.info(f"[Task] 배경 생성 완료 - Block ID: {block_id}, URL: {result['image_url']}")

        # 완료
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Completed",
            progress=1.0
        )

        return {
            "success": True,
            "block_id": block_id,
            "background_url": result['image_url'],
            "metadata": {
                "prompt": result['prompt'],
                "revised_prompt": result.get('revised_prompt'),
                "width": result['width'],
                "height": result['height']
            }
        }

    except Exception as e:
        logger.error(f"[Task] 배경 생성 실패 - Block ID: {block_id}: {e}")

        # 재시도
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="select_background_auto", bind=True, max_retries=3)
def select_background_auto_task(
    self: Task,
    block_id: int,
    campaign_id: Optional[int] = None,
    keywords: Optional[list[str]] = None,
    visual_concept: Optional[dict] = None,
    prefer_ai: bool = True
) -> dict:
    """
    배경 자동 선택 (3단계 우선순위 로직)

    Args:
        block_id: 스토리보드 블록 ID
        campaign_id: 캠페인 ID
        keywords: 배경 키워드
        visual_concept: 비주얼 컨셉
        prefer_ai: AI 우선 여부

    Returns:
        {
            "success": True,
            "block_id": 1,
            "background": {
                "background_type": "ai_generated",
                "background_url": "https://...",
                "source": "dall-e",
                "metadata": {...}
            }
        }
    """
    try:
        logger.info(f"[Task] 배경 자동 선택 시작 - Block ID: {block_id}")

        # 진행률 추적
        tracker = ProgressTracker()
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Selecting background",
            progress=0.1
        )

        # 배경 선택
        selector = BackgroundSelector()

        import asyncio
        background = asyncio.run(
            selector.select_background(
                campaign_id=campaign_id,
                keywords=keywords,
                visual_concept=visual_concept,
                prefer_ai=prefer_ai
            )
        )

        # 진행률 업데이트
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Background selected, updating database",
            progress=0.8
        )

        # TODO: SQLite에 업데이트
        # from app.lib.db import update_storyboard_block
        # update_storyboard_block(block_id, {
        #     "background_url": background['background_url'],
        #     "background_type": background['background_type'],
        #     "background_source": background['source'],
        #     "background_metadata": background['metadata']
        # })

        logger.info(
            f"[Task] 배경 선택 완료 - Block ID: {block_id}, "
            f"Type: {background['background_type']}, Source: {background['source']}"
        )

        # 완료
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Completed",
            progress=1.0
        )

        return {
            "success": True,
            "block_id": block_id,
            "background": background
        }

    except Exception as e:
        logger.error(f"[Task] 배경 선택 실패 - Block ID: {block_id}: {e}")

        # 재시도
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="batch_generate_backgrounds", bind=True)
def batch_generate_backgrounds_task(
    self: Task,
    blocks: list[dict],
    campaign_id: Optional[int] = None
) -> dict:
    """
    여러 블록의 배경을 일괄 생성

    Args:
        blocks: [{"block_id": 1, "keywords": [...], "visual_concept": {...}}, ...]
        campaign_id: 캠페인 ID

    Returns:
        {
            "success": True,
            "total": 10,
            "completed": 10,
            "failed": 0,
            "results": [...]
        }
    """
    try:
        logger.info(f"[Task] 배경 일괄 생성 시작 - {len(blocks)}개 블록")

        # 진행률 추적
        tracker = ProgressTracker()
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Batch background generation",
            progress=0.0
        )

        # 일괄 생성
        selector = BackgroundSelector()

        import asyncio
        results = asyncio.run(
            selector.batch_select_backgrounds(
                blocks=blocks,
                campaign_id=campaign_id
            )
        )

        # 통계
        total = len(results)
        completed = sum(1 for r in results if r.get("success"))
        failed = total - completed

        logger.info(
            f"[Task] 배경 일괄 생성 완료 - "
            f"Total: {total}, Completed: {completed}, Failed: {failed}"
        )

        # 완료
        tracker.update_task_progress(
            task_id=self.request.id,
            stage="Completed",
            progress=1.0
        )

        return {
            "success": True,
            "total": total,
            "completed": completed,
            "failed": failed,
            "results": results
        }

    except Exception as e:
        logger.error(f"[Task] 배경 일괄 생성 실패: {e}")
        raise
