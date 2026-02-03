"""
배경 이미지 생성 API
DALL-E & Unsplash 통합 엔드포인트
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.image_generation import ImageGenerationService
from app.services.stock_image import StockImageService
from app.services.background_selector import BackgroundSelector
from app.tasks.background_tasks import (
    generate_background_task,
    select_background_auto_task,
    batch_generate_backgrounds_task
)

router = APIRouter(prefix="/backgrounds", tags=["Backgrounds"])
logger = logging.getLogger(__name__)


# ==================== Request Models ====================

class GenerateImageRequest(BaseModel):
    """DALL-E 이미지 생성 요청"""
    block_id: int = Field(..., description="스토리보드 블록 ID")
    prompt: str = Field(..., min_length=10, max_length=500, description="DALL-E 프롬프트 (영문)")
    style: str = Field("natural", description="natural | vivid")
    size: str = Field("1024x1024", description="1024x1024 | 1792x1024 | 1024x1792")


class GenerateFromKeywordsRequest(BaseModel):
    """키워드 기반 이미지 생성 요청"""
    block_id: int = Field(..., description="스토리보드 블록 ID")
    keywords: list[str] = Field(..., min_items=1, max_items=10, description="배경 키워드")
    visual_concept: dict = Field(
        default_factory=lambda: {"mood": "professional", "color_tone": "neutral"},
        description="비주얼 컨셉 (mood, color_tone 등)"
    )
    style: str = Field("natural", description="natural | vivid")


class SelectBackgroundRequest(BaseModel):
    """배경 자동 선택 요청"""
    block_id: int = Field(..., description="스토리보드 블록 ID")
    campaign_id: Optional[int] = Field(None, description="캠페인 ID (리소스 검색용)")
    keywords: list[str] = Field(..., min_items=1, max_items=10, description="배경 키워드")
    visual_concept: dict = Field(
        default_factory=lambda: {"mood": "professional", "color_tone": "neutral"},
        description="비주얼 컨셉"
    )
    prefer_ai: bool = Field(True, description="True: AI 우선, False: 스톡 우선")


class BatchGenerateRequest(BaseModel):
    """배경 일괄 생성 요청"""
    blocks: list[dict] = Field(..., description="블록 정보 리스트")
    campaign_id: Optional[int] = Field(None, description="캠페인 ID")


# ==================== API Endpoints ====================

@router.post("/generate-dalle")
async def generate_dalle_image(request: GenerateImageRequest):
    """
    **DALL-E 이미지 생성 API (비동기)**

    프롬프트를 받아 DALL-E 3로 배경 이미지를 생성합니다.
    Celery 작업으로 실행되며, task_id를 반환합니다.

    **요청 필드**:
    - **block_id**: 스토리보드 블록 ID
    - **prompt**: DALL-E 프롬프트 (영문, 10-500자)
    - **style**: natural (자연스러움) | vivid (생동감)
    - **size**: 1024x1024 | 1792x1024 | 1024x1792

    **반환값**: Celery task_id
    """
    try:
        logger.info(f"DALL-E 생성 요청 - Block ID: {request.block_id}")

        # Celery 작업 시작
        task = generate_background_task.delay(
            block_id=request.block_id,
            prompt=request.prompt,
            style=request.style,
            size=request.size
        )

        return {
            "success": True,
            "task_id": task.id,
            "message": "배경 생성 작업이 시작되었습니다"
        }

    except Exception as e:
        logger.error(f"DALL-E 생성 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-keywords")
async def generate_from_keywords(request: GenerateFromKeywordsRequest):
    """
    **키워드 기반 이미지 생성 API**

    키워드와 비주얼 컨셉을 받아 GPT-4로 프롬프트를 최적화한 후,
    DALL-E 3로 이미지를 생성합니다.

    **요청 필드**:
    - **block_id**: 스토리보드 블록 ID
    - **keywords**: 배경 키워드 (1-10개)
    - **visual_concept**: {"mood": "energetic", "color_tone": "bright"}
    - **style**: natural | vivid

    **반환값**: 생성된 이미지 정보
    """
    try:
        logger.info(f"키워드 기반 생성 요청 - Keywords: {request.keywords}")

        service = ImageGenerationService()

        result = await service.generate_from_keywords(
            keywords=request.keywords,
            visual_concept=request.visual_concept,
            style=request.style
        )

        # TODO: SQLite에 저장
        # from app.lib.db import update_storyboard_block
        # update_storyboard_block(request.block_id, {
        #     "background_url": result['image_url'],
        #     "background_type": "ai_generated"
        # })

        return {
            "success": True,
            "block_id": request.block_id,
            "background_url": result['image_url'],
            "metadata": {
                "prompt": result['prompt'],
                "revised_prompt": result.get('revised_prompt'),
                "width": result['width'],
                "height": result['height']
            }
        }

    except Exception as e:
        logger.error(f"키워드 기반 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-unsplash")
async def search_unsplash_images(
    query: str = Query(..., min_length=2, description="검색 키워드 (영문)"),
    per_page: int = Query(10, ge=1, le=30, description="결과 개수 (최대 30)"),
    orientation: str = Query("landscape", description="landscape | portrait | squarish"),
    page: int = Query(1, ge=1, description="페이지 번호")
):
    """
    **Unsplash 이미지 검색 API**

    Unsplash에서 무료 스톡 이미지를 검색합니다.

    **쿼리 파라미터**:
    - **query**: 검색 키워드 (영문, 2자 이상)
    - **per_page**: 결과 개수 (1-30, 기본값 10)
    - **orientation**: landscape | portrait | squarish
    - **page**: 페이지 번호 (기본값 1)

    **반환값**: Unsplash 이미지 리스트
    """
    try:
        logger.info(f"Unsplash 검색 요청 - Query: {query}")

        service = StockImageService()

        results = await service.search_images(
            query=query,
            per_page=per_page,
            orientation=orientation,
            page=page
        )

        return {
            "success": True,
            "query": query,
            "total": len(results),
            "images": results
        }

    except Exception as e:
        logger.error(f"Unsplash 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select-auto")
async def select_background_auto(request: SelectBackgroundRequest):
    """
    **배경 자동 선택 API (3단계 우선순위)**

    1순위: 캠페인 리소스 라이브러리 (TODO)
    2순위: DALL-E AI 이미지 생성
    3순위: Unsplash 스톡 이미지
    Fallback: 단색 배경

    **요청 필드**:
    - **block_id**: 스토리보드 블록 ID
    - **campaign_id**: 캠페인 ID (선택)
    - **keywords**: 배경 키워드
    - **visual_concept**: 비주얼 컨셉
    - **prefer_ai**: True (AI 우선) | False (스톡 우선)

    **반환값**: Celery task_id
    """
    try:
        logger.info(f"배경 자동 선택 요청 - Block ID: {request.block_id}")

        # Celery 작업 시작
        task = select_background_auto_task.delay(
            block_id=request.block_id,
            campaign_id=request.campaign_id,
            keywords=request.keywords,
            visual_concept=request.visual_concept,
            prefer_ai=request.prefer_ai
        )

        return {
            "success": True,
            "task_id": task.id,
            "message": "배경 자동 선택 작업이 시작되었습니다"
        }

    except Exception as e:
        logger.error(f"배경 자동 선택 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate")
async def batch_generate_backgrounds(request: BatchGenerateRequest):
    """
    **배경 일괄 생성 API**

    여러 블록의 배경을 한 번에 생성합니다.

    **요청 필드**:
    - **blocks**: [{"block_id": 1, "keywords": [...], "visual_concept": {...}}, ...]
    - **campaign_id**: 캠페인 ID (선택)

    **반환값**: Celery task_id
    """
    try:
        logger.info(f"배경 일괄 생성 요청 - {len(request.blocks)}개 블록")

        # Celery 작업 시작
        task = batch_generate_backgrounds_task.delay(
            blocks=request.blocks,
            campaign_id=request.campaign_id
        )

        return {
            "success": True,
            "task_id": task.id,
            "total_blocks": len(request.blocks),
            "message": "배경 일괄 생성 작업이 시작되었습니다"
        }

    except Exception as e:
        logger.error(f"배경 일괄 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    **Celery 작업 상태 조회**

    배경 생성 작업의 진행 상황을 확인합니다.

    **경로 파라미터**:
    - **task_id**: Celery task ID

    **반환값**:
    - PENDING: 대기 중
    - STARTED: 실행 중
    - SUCCESS: 완료
    - FAILURE: 실패
    """
    from celery.result import AsyncResult

    try:
        result = AsyncResult(task_id)

        if result.state == "PENDING":
            return {
                "task_id": task_id,
                "state": "PENDING",
                "message": "작업 대기 중"
            }
        elif result.state == "STARTED":
            return {
                "task_id": task_id,
                "state": "STARTED",
                "message": "작업 실행 중",
                "progress": result.info.get("progress", 0) if result.info else 0
            }
        elif result.state == "SUCCESS":
            return {
                "task_id": task_id,
                "state": "SUCCESS",
                "message": "작업 완료",
                "result": result.result
            }
        elif result.state == "FAILURE":
            return {
                "task_id": task_id,
                "state": "FAILURE",
                "message": "작업 실패",
                "error": str(result.info)
            }
        else:
            return {
                "task_id": task_id,
                "state": result.state,
                "message": "알 수 없는 상태"
            }

    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
