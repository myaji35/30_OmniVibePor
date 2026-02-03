"""캠페인 관리 API

Studio 워크플로우의 캠페인 CRUD 엔드포인트입니다.
SQLite 구현 시 연결 가능하도록 인터페이스 설계되었습니다.

주요 기능:
- 캠페인 CRUD (생성, 조회, 수정, 삭제)
- 클라이언트별 캠페인 필터링
- 캠페인별 콘텐츠 스케줄 조회
- 리소스 업로드 (인트로/엔딩/BGM)
"""
from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate,
    Campaign,
    CampaignListResponse,
    ResourceUploadRequest,
    ResourceUploadResponse,
    CampaignStatus
)
from app.services.cloudinary_service import get_cloudinary_service
from app.db.sqlite_client import get_campaign_db, get_content_schedule_db

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
logger = logging.getLogger(__name__)


# ==================== API Endpoints ====================

@router.post("/", response_model=Campaign, status_code=201)
async def create_campaign(campaign: CampaignCreate):
    """
    **새 캠페인 생성**

    클라이언트를 위한 새로운 영상 제작 캠페인을 생성합니다.

    **요청 필드**:
    - **client_id**: 클라이언트 ID (필수)
    - **name**: 캠페인 이름 (필수)
    - **concept_gender**: 컨셉 성별 (female, male, neutral)
    - **concept_tone**: 컨셉 톤 (professional, friendly, humorous, serious)
    - **concept_style**: 컨셉 스타일 (soft, intense, calm, energetic)
    - **target_duration**: 목표 영상 길이 (초, 10-600)
    - **voice_id**: ElevenLabs Voice ID
    - **voice_name**: 음성 이름 (표시용)
    - **intro_video_url**: 인트로 영상 URL
    - **intro_duration**: 인트로 길이 (초, 0-10)
    - **outro_video_url**: 엔딩 영상 URL
    - **outro_duration**: 엔딩 길이 (초, 0-10)
    - **bgm_url**: 배경음악 URL
    - **bgm_volume**: BGM 볼륨 (0.0-1.0)
    - **publish_schedule**: 발행 스케줄
    - **auto_deploy**: 자동 배포 여부

    **반환값**: 생성된 캠페인 정보
    """
    try:
        campaign_db = get_campaign_db()

        # Campaign 데이터를 Dict로 변환
        campaign_data = campaign.model_dump()

        # SQLite에 저장
        campaign_id = await campaign_db.create(campaign_data)

        # 생성된 캠페인 조회
        created = await campaign_db.get_by_id(campaign_id)

        if not created:
            raise HTTPException(
                status_code=500,
                detail="Campaign created but could not be retrieved"
            )

        # Pydantic 모델로 변환
        return Campaign(**created)

    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=CampaignListResponse)
async def get_campaigns(
    client_id: Optional[int] = Query(None, description="클라이언트 ID 필터"),
    status: Optional[CampaignStatus] = Query(None, description="상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    **캠페인 목록 조회**

    캠페인 목록을 조회합니다. 클라이언트 ID나 상태로 필터링할 수 있습니다.

    **쿼리 파라미터**:
    - **client_id**: 특정 클라이언트의 캠페인만 조회
    - **status**: 특정 상태의 캠페인만 조회 (active, paused, completed, archived)
    - **page**: 페이지 번호 (기본: 1)
    - **page_size**: 페이지당 항목 수 (기본: 20, 최대: 100)

    **반환값**: 캠페인 목록 및 페이징 정보
    """
    try:
        campaign_db = get_campaign_db()

        # 총 개수 조회
        total = await campaign_db.count(
            client_id=client_id,
            status=status.value if status else None
        )

        # 페이징 계산
        offset = (page - 1) * page_size

        # 캠페인 목록 조회
        campaigns_data = await campaign_db.get_all(
            client_id=client_id,
            status=status.value if status else None,
            limit=page_size,
            offset=offset
        )

        # Pydantic 모델로 변환
        campaigns = [Campaign(**data) for data in campaigns_data]

        return CampaignListResponse(
            campaigns=campaigns,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to get campaigns: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: int):
    """
    **특정 캠페인 조회**

    캠페인 ID로 단일 캠페인 정보를 조회합니다.

    **경로 파라미터**:
    - **campaign_id**: 캠페인 ID

    **반환값**: 캠페인 상세 정보
    """
    try:
        campaign_db = get_campaign_db()
        campaign_data = await campaign_db.get_by_id(campaign_id)

        if not campaign_data:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        return Campaign(**campaign_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: int, updates: CampaignUpdate):
    """
    **캠페인 정보 업데이트**

    캠페인 정보를 부분적으로 수정합니다.

    **경로 파라미터**:
    - **campaign_id**: 캠페인 ID

    **요청 필드** (모두 선택):
    - **name**: 캠페인 이름
    - **concept_gender**: 컨셉 성별
    - **concept_tone**: 컨셉 톤
    - **concept_style**: 컨셉 스타일
    - **target_duration**: 목표 영상 길이
    - **voice_id**: ElevenLabs Voice ID
    - **voice_name**: 음성 이름
    - **intro_video_url**: 인트로 영상 URL
    - **intro_duration**: 인트로 길이
    - **outro_video_url**: 엔딩 영상 URL
    - **outro_duration**: 엔딩 길이
    - **bgm_url**: 배경음악 URL
    - **bgm_volume**: BGM 볼륨
    - **publish_schedule**: 발행 스케줄
    - **auto_deploy**: 자동 배포 여부
    - **status**: 캠페인 상태

    **반환값**: 수정된 캠페인 정보
    """
    try:
        campaign_db = get_campaign_db()

        # 캠페인 존재 확인
        existing = await campaign_db.get_by_id(campaign_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        # 수정할 필드만 추출
        update_data = updates.model_dump(exclude_unset=True)

        if not update_data:
            # 수정할 내용이 없으면 기존 정보 반환
            return Campaign(**existing)

        # SQLite 업데이트
        success = await campaign_db.update(campaign_id, update_data)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update campaign"
            )

        # 수정된 캠페인 조회
        updated = await campaign_db.get_by_id(campaign_id)
        return Campaign(**updated)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int):
    """
    **캠페인 삭제**

    캠페인 및 관련된 모든 데이터를 삭제합니다.

    **경로 파라미터**:
    - **campaign_id**: 삭제할 캠페인 ID

    **반환값**: 없음 (204 No Content)

    **주의**: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        campaign_db = get_campaign_db()

        # 캠페인 존재 확인
        existing = await campaign_db.get_by_id(campaign_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        # SQLite 삭제 (CASCADE로 관련 데이터 자동 삭제)
        success = await campaign_db.delete(campaign_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete campaign"
            )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{campaign_id}/schedule")
async def get_campaign_schedule(campaign_id: int):
    """
    **캠페인의 콘텐츠 스케줄 조회**

    캠페인에 속한 모든 콘텐츠 스케줄을 조회합니다.

    **경로 파라미터**:
    - **campaign_id**: 캠페인 ID

    **반환값**: 콘텐츠 스케줄 목록
    """
    try:
        campaign_db = get_campaign_db()
        content_db = get_content_schedule_db()

        # 캠페인 존재 확인
        campaign = await campaign_db.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        # 콘텐츠 스케줄 조회
        schedules = await content_db.get_by_campaign(campaign_id)

        return {
            "campaign_id": campaign_id,
            "schedules": schedules,
            "total": len(schedules)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{campaign_id}/resources")
async def upload_campaign_resources(
    campaign_id: int,
    intro: Optional[UploadFile] = File(None),
    outro: Optional[UploadFile] = File(None),
    bgm: Optional[UploadFile] = File(None)
):
    """
    **캠페인 리소스 일괄 업로드**

    인트로/엔딩 영상, BGM 등을 Cloudinary에 업로드합니다.
    여러 파일을 한 번에 업로드할 수 있습니다.

    **경로 파라미터**:
    - **campaign_id**: 캠페인 ID

    **폼 데이터** (모두 선택):
    - **intro**: 인트로 영상 파일
    - **outro**: 엔딩 영상 파일
    - **bgm**: 배경음악 파일

    **반환값**: 업로드된 리소스 정보 목록

    **지원 포맷**:
    - 비디오: mp4, mov, avi (intro, outro)
    - 오디오: mp3, wav, m4a (bgm)
    """
    try:
        campaign_db = get_campaign_db()

        # 캠페인 존재 확인
        campaign_data = await campaign_db.get_by_id(campaign_id)
        if not campaign_data:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        uploaded_resources = []
        updates = {}

        # 인트로 업로드
        if intro:
            result = await _upload_resource_file(
                campaign_id=campaign_id,
                file=intro,
                resource_type="intro"
            )
            updates["intro_video_url"] = result["url"]
            if result.get("duration"):
                updates["intro_duration"] = int(result["duration"])
            uploaded_resources.append(result)

        # 엔딩 업로드
        if outro:
            result = await _upload_resource_file(
                campaign_id=campaign_id,
                file=outro,
                resource_type="outro"
            )
            updates["outro_video_url"] = result["url"]
            if result.get("duration"):
                updates["outro_duration"] = int(result["duration"])
            uploaded_resources.append(result)

        # BGM 업로드
        if bgm:
            result = await _upload_resource_file(
                campaign_id=campaign_id,
                file=bgm,
                resource_type="bgm"
            )
            updates["bgm_url"] = result["url"]
            uploaded_resources.append(result)

        # 캠페인 업데이트
        if updates:
            await campaign_db.update(campaign_id, updates)

        logger.info(
            f"Resources uploaded for campaign {campaign_id}: "
            f"{len(uploaded_resources)} file(s)"
        )

        return {
            "campaign_id": campaign_id,
            "uploaded": uploaded_resources,
            "total": len(uploaded_resources)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload campaign resources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


async def _upload_resource_file(
    campaign_id: int,
    file: UploadFile,
    resource_type: str
) -> dict:
    """
    단일 리소스 파일 업로드 헬퍼 함수
    """
    import tempfile
    from pathlib import Path

    # 파일 임시 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        cloudinary_service = get_cloudinary_service()

        # Cloudinary 업로드
        result = await cloudinary_service.upload_video(
            video_path=tmp_path,
            folder=f"campaigns/{campaign_id}/{resource_type}",
            public_id=f"campaign_{campaign_id}_{resource_type}",
            project_id=str(campaign_id)
        )

        logger.info(
            f"Resource uploaded: {resource_type} for campaign {campaign_id} -> {result['secure_url']}"
        )

        return {
            "resource_type": resource_type,
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "duration": result.get("duration"),
            "format": result.get("format")
        }

    finally:
        # 임시 파일 삭제
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/{campaign_id}/resources")
async def get_campaign_resources(campaign_id: int):
    """
    **캠페인 리소스 조회**

    캠페인의 모든 리소스(인트로/엔딩/BGM) 정보를 조회합니다.

    **경로 파라미터**:
    - **campaign_id**: 캠페인 ID

    **반환값**: 리소스 정보
    """
    try:
        campaign_db = get_campaign_db()
        campaign_data = await campaign_db.get_by_id(campaign_id)

        if not campaign_data:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign not found: {campaign_id}"
            )

        return {
            "campaign_id": campaign_id,
            "resources": {
                "intro": {
                    "url": campaign_data.get("intro_video_url"),
                    "duration": campaign_data.get("intro_duration")
                } if campaign_data.get("intro_video_url") else None,
                "outro": {
                    "url": campaign_data.get("outro_video_url"),
                    "duration": campaign_data.get("outro_duration")
                } if campaign_data.get("outro_video_url") else None,
                "bgm": {
                    "url": campaign_data.get("bgm_url"),
                    "volume": campaign_data.get("bgm_volume")
                } if campaign_data.get("bgm_url") else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign resources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
