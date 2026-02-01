"""Continuity API 엔드포인트"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.services.continuity_agent import get_continuity_agent
from app.services.resource_manager import get_resource_manager, Resource
from app.services.google_sheets_service import get_sheets_service

router = APIRouter(prefix="/continuity", tags=[" Continuity"])
logger = logging.getLogger(__name__)


class ContinuityGenerationRequest(BaseModel):
    """콘티 생성 요청"""
    script: str
    campaign_name: str
    topic: str
    platform: str = "YouTube"  # YouTube, Instagram, TikTok
    mode: str = "auto"  # "auto" | "manual" | "hybrid"
    spreadsheet_id: Optional[str] = None  # 구글 시트 ID (리소스 자동 로드)
    resource_urls: Optional[List[str]] = None  # 리소스 URL 목록 (옵션)


class SceneData(BaseModel):
    """씬 데이터"""
    scene_number: int
    start_time: float
    end_time: float
    duration: float
    script_text: str
    camera_work: str
    resource_ids: List[str] = []
    bgm_file: Optional[str] = None
    sfx_file: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ContinuityResponse(BaseModel):
    """콘티 생성 응답"""
    success: bool
    campaign_name: Optional[str] = None
    topic: Optional[str] = None
    platform: Optional[str] = None
    total_duration: Optional[float] = None
    scene_count: Optional[int] = None
    scenes: Optional[List[SceneData]] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=ContinuityResponse)
async def generate_continuity(request: ContinuityGenerationRequest):
    """
    콘티 자동 생성

    LangGraph 기반 Continuity Agent가:
    1. 스크립트를 씬으로 자동 분할
    2. 각 씬의 카메라 워크 제안
    3. 리소스 자동 매핑
    4. Neo4j에 저장

    Args:
        script: 스크립트 텍스트
        campaign_name: 캠페인명
        topic: 소제목
        platform: 플랫폼 (YouTube, Instagram, TikTok)
        mode: "auto" (자동) | "manual" (수동) | "hybrid" (혼합)
        resource_urls: 리소스 URL 목록

    Returns:
        생성된 콘티 정보
    """
    continuity_agent = get_continuity_agent()
    sheets_service = get_sheets_service()

    try:
        # 구글 시트에서 리소스 자동 로드 (옵션)
        resources = None
        if request.spreadsheet_id:
            try:
                # 캠페인명 + 소제목으로 필터링하여 리소스 로드
                resources = await sheets_service.read_resources_sheet(
                    spreadsheet_id=request.spreadsheet_id,
                    campaign_name=request.campaign_name,
                    topic=request.topic
                )
                logger.info(f"Loaded {len(resources)} resources from Google Sheets")
            except Exception as e:
                logger.warning(f"Failed to load resources from Google Sheets: {e}")
                # 리소스 로드 실패해도 계속 진행 (리소스 없이 콘티 생성)
                resources = None

        result = await continuity_agent.generate_continuity(
            script=request.script,
            campaign_name=request.campaign_name,
            topic=request.topic,
            platform=request.platform,
            resources=resources,
            mode=request.mode
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "콘티 생성에 실패했습니다")
            )

        # 씬 데이터를 Pydantic 모델로 변환
        scenes_data = [
            SceneData(**scene)
            for scene in result["scenes"]
        ]

        return ContinuityResponse(
            success=True,
            campaign_name=result["campaign_name"],
            topic=result["topic"],
            platform=result["platform"],
            total_duration=result["total_duration"],
            scene_count=result["scene_count"],
            scenes=scenes_data,
            created_at=result["created_at"]
        )

    except Exception as e:
        logger.error(f"Continuity generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"콘티 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/upload-resource")
async def upload_resource(
    file: UploadFile = File(...),
    campaign_name: Optional[str] = None
):
    """
    리소스 업로드

    Args:
        file: 업로드할 파일 (이미지, PDF, 영상)
        campaign_name: 캠페인명 (옵션)

    Returns:
        업로드된 리소스 정보
    """
    resource_manager = get_resource_manager()

    try:
        # 파일 읽기
        file_data = await file.read()

        # 리소스 업로드
        resource = await resource_manager.upload_resource(
            file_data=file_data,
            filename=file.filename,
            campaign_name=campaign_name
        )

        return {
            "success": True,
            "resource": {
                "id": resource.id,
                "type": resource.type,
                "name": resource.name,
                "url": resource.url,
                "size_bytes": resource.size_bytes,
                "created_at": resource.created_at
            }
        }

    except Exception as e:
        logger.error(f"Resource upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"리소스 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/convert-pdf")
async def convert_pdf_to_images(
    file: UploadFile = File(...),
    campaign_name: Optional[str] = None
):
    """
    PDF → 이미지 변환

    PDF 파일을 페이지별 이미지로 변환합니다.

    Args:
        file: PDF 파일
        campaign_name: 캠페인명 (옵션)

    Returns:
        변환된 이미지 리소스 목록
    """
    resource_manager = get_resource_manager()

    try:
        # 파일 읽기
        pdf_data = await file.read()

        # PDF → 이미지 변환
        image_resources = await resource_manager.convert_pdf_to_images(
            pdf_data=pdf_data,
            campaign_name=campaign_name
        )

        return {
            "success": True,
            "total_images": len(image_resources),
            "images": [
                {
                    "id": res.id,
                    "name": res.name,
                    "url": res.url,
                    "size_bytes": res.size_bytes
                }
                for res in image_resources
            ]
        }

    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF 변환 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def check_health():
    """
    Continuity Agent 상태 확인
    """
    try:
        continuity_agent = get_continuity_agent()
        return {
            "status": "healthy",
            "message": "Continuity agent is ready",
            "llm_model": "claude-3-haiku-20240307"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }
