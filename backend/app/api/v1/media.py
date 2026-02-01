"""Cloudinary 미디어 최적화 API 엔드포인트"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.cloudinary_service import get_cloudinary_service, PLATFORM_TRANSFORMATIONS

router = APIRouter()
logger = logging.getLogger(__name__)


class VideoUploadResponse(BaseModel):
    """영상 업로드 응답"""
    public_id: str
    url: str
    secure_url: str
    format: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bytes: int


class ImageUploadResponse(BaseModel):
    """이미지 업로드 응답"""
    public_id: str
    url: str
    secure_url: str
    format: str
    width: Optional[int] = None
    height: Optional[int] = None
    bytes: int


class TransformRequest(BaseModel):
    """영상 변환 요청"""
    public_id: str = Field(..., description="Cloudinary public ID")
    platform: str = Field(..., description="플랫폼명 (youtube, instagram_feed, tiktok 등)")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    project_id: Optional[str] = Field(None, description="프로젝트 ID")


class ThumbnailRequest(BaseModel):
    """썸네일 생성 요청"""
    video_public_id: str = Field(..., description="영상 public ID")
    time_offset: float = Field(0.0, ge=0.0, description="썸네일 추출 시간 (초)")
    width: int = Field(1280, ge=100, le=4096, description="썸네일 너비")
    height: int = Field(720, ge=100, le=4096, description="썸네일 높이")
    download: bool = Field(False, description="파일 다운로드 여부")
    user_id: Optional[str] = None
    project_id: Optional[str] = None


class OptimizedUrlRequest(BaseModel):
    """최적화된 URL 생성 요청"""
    public_id: str = Field(..., description="Cloudinary public ID")
    resource_type: str = Field("image", description="리소스 타입 (image, video)")
    format: Optional[str] = Field(None, description="파일 포맷")


@router.get("/platforms")
async def get_supported_platforms():
    """
    지원하는 플랫폼 목록 조회

    **응답**: 플랫폼별 변환 설정
    """
    platforms = {}
    for platform, config in PLATFORM_TRANSFORMATIONS.items():
        platforms[platform] = {
            "resolution": f"{config['width']}x{config['height']}",
            "aspect_ratio": config['aspect_ratio'],
            "quality": config['quality'],
            "format": config['format']
        }

    return {
        "platforms": platforms,
        "count": len(platforms)
    }


@router.post("/upload/video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(..., description="업로드할 영상 파일"),
    public_id: Optional[str] = Form(None, description="Cloudinary public ID (자동 생성)"),
    folder: str = Form("videos", description="저장 폴더"),
    user_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None)
):
    """
    영상 업로드

    **지원 포맷**: MP4, MOV, AVI, MKV 등
    **최대 크기**: 100MB (Free tier 기준)

    **자동 변환**:
    - 1920x1080 해상도로 사전 변환
    - 자동 품질 최적화
    """
    service = get_cloudinary_service()

    try:
        # 임시 파일 저장
        temp_path = Path(service.output_dir) / f"temp_{file.filename}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Uploading video: {file.filename} ({len(content) / 1024 / 1024:.2f} MB)")

        # Cloudinary 업로드
        result = await service.upload_video(
            video_path=str(temp_path),
            public_id=public_id,
            folder=folder,
            user_id=user_id,
            project_id=project_id
        )

        # 임시 파일 삭제
        temp_path.unlink(missing_ok=True)

        return VideoUploadResponse(**result)

    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    public_id: Optional[str] = Form(None),
    folder: str = Form("images"),
    user_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None)
):
    """
    이미지 업로드

    **지원 포맷**: JPG, PNG, GIF, WebP 등
    **최대 크기**: 10MB

    **자동 최적화**:
    - 자동 포맷 변환 (WebP, AVIF 등)
    - 품질 자동 조정
    """
    service = get_cloudinary_service()

    try:
        # 임시 파일 저장
        temp_path = Path(service.output_dir) / f"temp_{file.filename}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Uploading image: {file.filename} ({len(content) / 1024:.2f} KB)")

        # Cloudinary 업로드
        result = await service.upload_image(
            image_path=str(temp_path),
            public_id=public_id,
            folder=folder,
            user_id=user_id,
            project_id=project_id
        )

        # 임시 파일 삭제
        temp_path.unlink(missing_ok=True)

        return ImageUploadResponse(**result)

    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform/video")
async def transform_video(request: TransformRequest):
    """
    플랫폼별 영상 변환

    **지원 플랫폼**:
    - youtube: 1920x1080 (16:9)
    - instagram_feed: 1080x1080 (1:1)
    - instagram_story: 1080x1920 (9:16)
    - instagram_reels: 1080x1920 (9:16)
    - tiktok: 1080x1920 (9:16)
    - facebook: 1280x720 (16:9)

    **반환**: 변환된 영상 파일 경로
    """
    service = get_cloudinary_service()

    try:
        # 플랫폼 검증
        if request.platform not in PLATFORM_TRANSFORMATIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown platform: {request.platform}. "
                       f"Supported: {list(PLATFORM_TRANSFORMATIONS.keys())}"
            )

        logger.info(f"Transforming video {request.public_id} for {request.platform}")

        # 영상 변환
        output_path = await service.transform_video_for_platform(
            public_id=request.public_id,
            platform=request.platform,
            user_id=request.user_id,
            project_id=request.project_id
        )

        config = PLATFORM_TRANSFORMATIONS[request.platform]

        return {
            "status": "success",
            "platform": request.platform,
            "resolution": f"{config['width']}x{config['height']}",
            "aspect_ratio": config['aspect_ratio'],
            "output_path": output_path,
            "message": f"{request.platform}용 영상 변환 완료"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video transformation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thumbnail/generate")
async def generate_thumbnail(request: ThumbnailRequest):
    """
    영상에서 썸네일 생성

    **사용 예시**:
    - 영상 시작 부분 썸네일: time_offset=0
    - 중간 부분 썸네일: time_offset=영상길이/2
    - 특정 장면 썸네일: time_offset=원하는 시간(초)

    **반환**: 썸네일 URL (또는 파일)
    """
    service = get_cloudinary_service()

    try:
        logger.info(
            f"Generating thumbnail from {request.video_public_id} "
            f"at {request.time_offset}s"
        )

        # 썸네일 생성
        output_path = None
        if request.download:
            output_path = str(
                Path(service.output_dir) / f"thumbnail_{request.video_public_id}_{request.time_offset}s.jpg"
            )

        thumbnail_url = await service.generate_thumbnail(
            video_public_id=request.video_public_id,
            time_offset=request.time_offset,
            width=request.width,
            height=request.height,
            output_path=output_path,
            user_id=request.user_id,
            project_id=request.project_id
        )

        response = {
            "status": "success",
            "thumbnail_url": thumbnail_url,
            "resolution": f"{request.width}x{request.height}",
            "time_offset": request.time_offset
        }

        if output_path:
            response["local_path"] = output_path

        return response

    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url/optimized")
async def get_optimized_url(request: OptimizedUrlRequest):
    """
    최적화된 URL 생성

    **자동 최적화**:
    - 품질 자동 조정
    - 포맷 자동 변환 (WebP, AVIF)
    - 다양한 기기 대응
    """
    service = get_cloudinary_service()

    try:
        url = service.get_optimized_url(
            public_id=request.public_id,
            resource_type=request.resource_type,
            format=request.format
        )

        return {
            "status": "success",
            "public_id": request.public_id,
            "optimized_url": url,
            "resource_type": request.resource_type
        }

    except Exception as e:
        logger.error(f"Failed to generate optimized URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/asset/{public_id}")
async def delete_asset(
    public_id: str,
    resource_type: str = "video"
):
    """
    에셋 삭제

    **주의**: 삭제된 에셋은 복구할 수 없습니다.
    """
    service = get_cloudinary_service()

    try:
        logger.info(f"Deleting {resource_type}: {public_id}")

        success = await service.delete_asset(
            public_id=public_id,
            resource_type=resource_type
        )

        if success:
            return {
                "status": "success",
                "message": f"Asset {public_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Asset {public_id} not found or already deleted"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/asset/{public_id}")
async def get_asset_info(
    public_id: str,
    resource_type: str = "video"
):
    """
    에셋 정보 조회

    **반환**:
    - 포맷, 해상도, 크기, 길이 등
    """
    service = get_cloudinary_service()

    try:
        info = await service.get_asset_info(
            public_id=public_id,
            resource_type=resource_type
        )

        return {
            "status": "success",
            "asset": info
        }

    except Exception as e:
        logger.error(f"Failed to get asset info: {e}")
        raise HTTPException(status_code=404, detail=f"Asset {public_id} not found")
