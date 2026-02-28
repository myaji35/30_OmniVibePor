"""멀티포맷 렌더링 API 라우터

영상 렌더링 시작, 상태 조회, 결과 URL 조회 엔드포인트:
- POST /render/start: 렌더링 시작
- GET /render/{task_id}/status: 상태 조회
- GET /render/{task_id}/result: 결과 URL 조회
"""
from fastapi import APIRouter, HTTPException
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/render", tags=["render"])

try:
    from app.models.render import RenderRequest, RenderStatus
    from app.tasks.render_tasks import render_video_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


@router.post("/start", response_model=dict)
async def start_render(request: RenderRequest):
    """영상 렌더링 시작"""
    try:
        task_id = str(uuid.uuid4())

        if CELERY_AVAILABLE:
            task = render_video_task.delay(request.dict())
            task_id = task.id

        return {
            "task_id": task_id,
            "status": "pending",
            "message": "렌더링 작업이 시작되었습니다",
            "formats": [f.value for f in request.formats]
        }
    except Exception as e:
        logger.error(f"Render start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status", response_model=RenderStatus)
async def get_render_status(task_id: str):
    """렌더링 상태 조회"""
    try:
        if CELERY_AVAILABLE:
            from celery.result import AsyncResult
            from app.tasks.celery_app import celery_app
            result = AsyncResult(task_id, app=celery_app)

            if result.state == 'PENDING':
                return RenderStatus(task_id=task_id, status="pending", progress=0)
            elif result.state == 'PROGRESS':
                meta = result.info or {}
                return RenderStatus(
                    task_id=task_id,
                    status="in_progress",
                    progress=meta.get('progress', 0),
                    format=meta.get('current_format')
                )
            elif result.state == 'SUCCESS':
                info = result.result or {}
                return RenderStatus(
                    task_id=task_id,
                    status="completed",
                    progress=100,
                    output_url=str(info.get('results', {}).get('youtube', ''))
                )
            elif result.state == 'FAILURE':
                return RenderStatus(
                    task_id=task_id,
                    status="failed",
                    progress=0,
                    error=str(result.info)
                )

        return RenderStatus(task_id=task_id, status="pending", progress=0)

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/result")
async def get_render_result(task_id: str):
    """렌더링 결과 URL 조회"""
    try:
        if CELERY_AVAILABLE:
            from celery.result import AsyncResult
            from app.tasks.celery_app import celery_app
            result = AsyncResult(task_id, app=celery_app)

            if result.state == 'SUCCESS':
                return result.result

        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
