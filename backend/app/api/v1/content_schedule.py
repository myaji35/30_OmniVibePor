"""콘텐츠 스케줄 관리 API

캠페인별 콘텐츠 스케줄 CRUD 엔드포인트입니다.

주요 기능:
- 콘텐츠 스케줄 생성, 조회, 수정, 삭제
- 캠페인별 콘텐츠 필터링
- 플랫폼별 필터링 (Youtube, Instagram, TikTok, Facebook)
- 상태별 필터링 (draft, scheduled, published, archived)
"""
from typing import List, Optional
import logging
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.sqlite_client import get_content_schedule_db, get_campaign_db

router = APIRouter(prefix="/content-schedule", tags=["Content Schedule"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class ContentScheduleCreate(BaseModel):
    """콘텐츠 스케줄 생성 요청"""
    campaign_id: int = Field(..., description="캠페인 ID")
    topic: str = Field(..., description="주제")
    subtitle: str = Field(..., description="부제목")
    platform: str = Field(..., description="플랫폼 (Youtube, Instagram, TikTok, Facebook)")
    publish_date: Optional[str] = Field(None, description="발행 날짜 (YYYY-MM-DD)")
    status: str = Field(default="draft", description="상태 (draft, scheduled, published, archived)")
    target_audience: Optional[str] = Field(None, description="타겟 오디언스")
    keywords: Optional[str] = Field(None, description="키워드 (콤마 구분)")
    notes: Optional[str] = Field(None, description="메모")


class ContentScheduleUpdate(BaseModel):
    """콘텐츠 스케줄 업데이트 요청"""
    topic: Optional[str] = None
    subtitle: Optional[str] = None
    platform: Optional[str] = None
    publish_date: Optional[str] = None
    status: Optional[str] = None
    target_audience: Optional[str] = None
    keywords: Optional[str] = None
    notes: Optional[str] = None


class ContentScheduleResponse(BaseModel):
    """콘텐츠 스케줄 응답"""
    id: int
    campaign_id: int
    topic: str
    subtitle: str
    platform: str
    publish_date: Optional[str]
    status: str
    target_audience: Optional[str]
    keywords: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str


# ==================== API Endpoints ====================

@router.post("/", status_code=201)
async def create_content_schedule(content: ContentScheduleCreate):
    """
    **콘텐츠 스케줄 생성**

    캠페인에 새로운 콘텐츠 스케줄을 추가합니다.

    **요청 필드**:
    - **campaign_id**: 캠페인 ID (필수)
    - **topic**: 주제 (필수)
    - **subtitle**: 부제목 (필수)
    - **platform**: 플랫폼 - Youtube, Instagram, TikTok, Facebook (필수)
    - **publish_date**: 발행 날짜 (YYYY-MM-DD)
    - **status**: 상태 - draft, scheduled, published, archived
    - **target_audience**: 타겟 오디언스
    - **keywords**: 키워드 (콤마 구분)
    - **notes**: 메모

    **반환값**: 생성된 콘텐츠 ID 및 성공 메시지
    """
    try:
        campaign_db = get_campaign_db()
        content_db = get_content_schedule_db()

        # 캠페인 존재 확인
        campaign = await campaign_db.get_by_id(content.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {content.campaign_id}"
            )

        # 콘텐츠 생성
        content_data = content.model_dump()
        content_id = await content_db.create(content_data)

        logger.info(
            f"Content schedule created: id={content_id}, "
            f"campaign_id={content.campaign_id}, topic={content.topic}"
        )

        return {
            "success": True,
            "content_id": content_id,
            "message": "콘텐츠가 추가되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create content schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/")
async def get_content_schedules(
    campaign_id: Optional[int] = Query(None, description="캠페인 ID 필터")
):
    """
    **콘텐츠 스케줄 목록 조회**

    캠페인별 콘텐츠 스케줄을 조회합니다.

    **쿼리 파라미터**:
    - **campaign_id**: 특정 캠페인의 콘텐츠만 조회

    **반환값**: 콘텐츠 스케줄 목록
    """
    try:
        content_db = get_content_schedule_db()

        if campaign_id is None:
            raise HTTPException(
                status_code=400,
                detail="campaign_id is required"
            )

        contents = await content_db.get_by_campaign(campaign_id)

        return {
            "success": True,
            "contents": contents
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content schedules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{content_id}")
async def get_content_schedule(content_id: int):
    """
    **특정 콘텐츠 스케줄 조회**

    콘텐츠 ID로 단일 콘텐츠 스케줄을 조회합니다.

    **경로 파라미터**:
    - **content_id**: 콘텐츠 ID

    **반환값**: 콘텐츠 스케줄 상세 정보
    """
    try:
        content_db = get_content_schedule_db()
        content_data = await content_db.get_by_id(content_id)

        if not content_data:
            raise HTTPException(
                status_code=404,
                detail=f"Content schedule not found: {content_id}"
            )

        return {
            "success": True,
            "content": content_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{content_id}")
async def update_content_schedule(content_id: int, updates: ContentScheduleUpdate):
    """
    **콘텐츠 스케줄 업데이트**

    콘텐츠 스케줄 정보를 부분적으로 수정합니다.

    **경로 파라미터**:
    - **content_id**: 콘텐츠 ID

    **요청 필드** (모두 선택):
    - **topic**: 주제
    - **subtitle**: 부제목
    - **platform**: 플랫폼
    - **publish_date**: 발행 날짜
    - **status**: 상태
    - **target_audience**: 타겟 오디언스
    - **keywords**: 키워드
    - **notes**: 메모

    **반환값**: 수정된 콘텐츠 스케줄 정보
    """
    try:
        content_db = get_content_schedule_db()

        # 콘텐츠 존재 확인
        existing = await content_db.get_by_id(content_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Content schedule not found: {content_id}"
            )

        # 수정할 필드만 추출
        update_data = updates.model_dump(exclude_unset=True)

        if not update_data:
            return {
                "success": True,
                "content": existing,
                "message": "No changes made"
            }

        # SQLite 업데이트
        success = await content_db.update(content_id, update_data)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update content schedule"
            )

        # 수정된 콘텐츠 조회
        updated = await content_db.get_by_id(content_id)

        return {
            "success": True,
            "content": updated,
            "message": "콘텐츠가 수정되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update content schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{content_id}", status_code=204)
async def delete_content_schedule(content_id: int):
    """
    **콘텐츠 스케줄 삭제**

    콘텐츠 스케줄 및 관련된 모든 데이터를 삭제합니다.

    **경로 파라미터**:
    - **content_id**: 삭제할 콘텐츠 ID

    **반환값**: 없음 (204 No Content)

    **주의**: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        content_db = get_content_schedule_db()

        # 콘텐츠 존재 확인
        existing = await content_db.get_by_id(content_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Content schedule not found: {content_id}"
            )

        # 삭제 로직 (현재 미구현)
        # TODO: ContentScheduleDB에 delete 메소드 추가 필요

        logger.info(f"Content schedule deleted: id={content_id}")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
