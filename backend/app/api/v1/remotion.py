"""Remotion API 엔드포인트

Remotion 기반 영상 렌더링:
- Storyboard → Remotion Props 변환
- 비동기 렌더링 (Celery)
- 렌더링 상태 조회
- Composition 목록 조회
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from celery.result import AsyncResult
import logging

from app.tasks.celery_app import celery_app
from app.tasks.video_tasks import (
    render_video_with_remotion_task,
    validate_remotion_setup_task,
    batch_render_videos_task
)
from app.services.remotion_service import get_remotion_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Request/Response Models ====================

class RenderRequest(BaseModel):
    """영상 렌더링 요청"""
    content_id: int = Field(..., description="콘텐츠 ID")
    storyboard_blocks: List[Dict[str, Any]] = Field(
        ...,
        description="Director Agent가 생성한 콘티 블록 리스트"
    )
    campaign_concept: Dict[str, str] = Field(
        ...,
        description="캠페인 컨셉 (gender, tone, style, platform)"
    )
    audio_url: Optional[str] = Field(
        None,
        description="Zero-Fault Audio Director 출력 URL"
    )
    composition_id: str = Field(
        "OmniVibeComposition",
        description="Remotion composition ID"
    )

    class Config:
        schema_extra = {
            "example": {
                "content_id": 123,
                "storyboard_blocks": [
                    {
                        "block_type": "hook",
                        "text": "여러분, 오늘은 특별한 소식이 있습니다!",
                        "duration": 5,
                        "visual_concept": "energetic intro",
                        "background_url": "https://images.unsplash.com/photo-123",
                        "transition_effect": "fade"
                    },
                    {
                        "block_type": "body",
                        "text": "우리 제품이 드디어 출시되었습니다.",
                        "duration": 10,
                        "visual_concept": "product showcase",
                        "background_url": "https://images.unsplash.com/photo-456",
                        "transition_effect": "wipeleft"
                    }
                ],
                "campaign_concept": {
                    "gender": "male",
                    "tone": "professional",
                    "style": "cinematic",
                    "platform": "YouTube"
                },
                "audio_url": "https://res.cloudinary.com/omnivibe/audio_123.mp3",
                "composition_id": "OmniVibeComposition"
            }
        }


class RenderResponse(BaseModel):
    """렌더링 응답"""
    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(..., description="작업 상태 (processing)")
    message: str = Field(..., description="상태 메시지")


class RenderStatusResponse(BaseModel):
    """렌더링 상태 응답"""
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class BatchRenderRequest(BaseModel):
    """배치 렌더링 요청"""
    render_requests: List[Dict[str, Any]] = Field(
        ...,
        description="렌더링 요청 리스트"
    )


class CompositionInfo(BaseModel):
    """Composition 정보"""
    id: str
    name: str
    description: str
    defaultProps: Dict[str, Any]


# ==================== API Endpoints ====================

@router.post(
    "/remotion/render",
    response_model=RenderResponse,
    summary="🎬 Remotion 영상 렌더링",
    description="""
    Director Agent의 Storyboard Blocks를 Remotion으로 렌더링합니다.

    **워크플로우:**
    1. Storyboard Blocks → Remotion Props 변환
    2. Celery 비동기 렌더링 작업 시작
    3. Remotion CLI 실행 (React 기반)
    4. Cloudinary 자동 업로드
    5. WebSocket으로 실시간 진행 상태 업데이트

    **특징:**
    - Platform-specific optimization (YouTube, Instagram, TikTok)
    - Professional video quality
    - Dynamic composition rendering
    - Audio synchronization
    """
)
async def render_video_with_remotion(request: RenderRequest):
    """Remotion 기반 영상 렌더링 (비동기)"""
    try:
        logger.info(f"🎬 Starting Remotion render - content_id: {request.content_id}")

        # Celery Task 시작
        task = render_video_with_remotion_task.delay(
            content_id=request.content_id,
            storyboard_blocks=request.storyboard_blocks,
            campaign_concept=request.campaign_concept,
            audio_url=request.audio_url,
            composition_id=request.composition_id
        )

        return RenderResponse(
            task_id=task.id,
            status="processing",
            message=f"Remotion 렌더링 시작. Task ID: {task.id}로 상태를 조회하세요."
        )

    except Exception as e:
        logger.error(f"❌ Failed to start Remotion render: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/remotion/status/{task_id}",
    response_model=RenderStatusResponse,
    summary="📊 렌더링 상태 조회",
    description="Remotion 렌더링 작업의 현재 상태를 조회합니다."
)
async def get_render_status(task_id: str):
    """렌더링 상태 조회"""
    try:
        task = AsyncResult(task_id, app=celery_app)

        if task.state == "PENDING":
            return RenderStatusResponse(
                task_id=task_id,
                status="pending",
                message="작업이 대기 중입니다."
            )
        elif task.state == "PROGRESS":
            info = task.info or {}
            return RenderStatusResponse(
                task_id=task_id,
                status="processing",
                progress=info.get("progress", 0),
                message=info.get("message", "렌더링 진행 중...")
            )
        elif task.state == "SUCCESS":
            result = task.result
            return RenderStatusResponse(
                task_id=task_id,
                status="completed",
                progress=100,
                message="렌더링 완료!",
                result=result
            )
        else:  # FAILURE
            return RenderStatusResponse(
                task_id=task_id,
                status="failed",
                message=f"렌더링 실패: {str(task.info)}"
            )

    except Exception as e:
        logger.error(f"❌ Failed to get render status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/remotion/compositions",
    response_model=List[CompositionInfo],
    summary="📋 Composition 목록 조회",
    description="사용 가능한 Remotion Composition 목록을 조회합니다."
)
async def get_compositions():
    """Composition 목록 조회"""
    try:
        remotion_service = get_remotion_service()
        compositions = remotion_service.get_available_compositions()

        return [
            CompositionInfo(**comp)
            for comp in compositions
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get compositions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/remotion/validate",
    summary="✅ Remotion 설정 검증",
    description="Remotion CLI 설치 상태 및 설정을 검증합니다."
)
async def validate_remotion_setup():
    """Remotion 설정 검증"""
    try:
        task = validate_remotion_setup_task.delay()
        result = task.get(timeout=10)  # 10초 대기

        if result.get("status") == "ok":
            return {
                "status": "ok",
                "message": "✅ Remotion 설정이 정상입니다.",
                "details": result
            }
        else:
            return {
                "status": "error",
                "message": "❌ Remotion 설정에 문제가 있습니다.",
                "details": result
            }

    except Exception as e:
        logger.error(f"❌ Failed to validate Remotion setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/remotion/batch-render",
    response_model=RenderResponse,
    summary="🎬 배치 영상 렌더링",
    description="여러 영상을 한 번에 렌더링합니다."
)
async def batch_render_videos(request: BatchRenderRequest):
    """배치 렌더링"""
    try:
        logger.info(f"🎬 Starting batch render - count: {len(request.render_requests)}")

        task = batch_render_videos_task.delay(
            render_requests=request.render_requests
        )

        return RenderResponse(
            task_id=task.id,
            status="processing",
            message=f"{len(request.render_requests)}개 영상 배치 렌더링 시작. Task ID: {task.id}"
        )

    except Exception as e:
        logger.error(f"❌ Failed to start batch render: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/remotion/convert-props",
    summary="🔄 Storyboard → Props 변환",
    description="Director Agent의 Storyboard Blocks를 Remotion Props로 변환합니다 (렌더링 없이 변환만)."
)
async def convert_storyboard_to_props(
    storyboard_blocks: List[Dict[str, Any]],
    campaign_concept: Dict[str, str],
    audio_url: Optional[str] = None
):
    """Storyboard → Remotion Props 변환 (렌더링 없이)"""
    try:
        remotion_service = get_remotion_service()
        props = remotion_service.convert_storyboard_to_props(
            storyboard_blocks=storyboard_blocks,
            campaign_concept=campaign_concept,
            audio_url=audio_url
        )

        return {
            "status": "success",
            "props": props,
            "message": f"✅ {len(storyboard_blocks)}개 블록이 Remotion Props로 변환되었습니다."
        }

    except Exception as e:
        logger.error(f"❌ Failed to convert props: {e}")
        raise HTTPException(status_code=500, detail=str(e))
