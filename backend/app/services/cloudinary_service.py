"""Cloudinary 미디어 최적화 서비스

Cloudinary를 사용한 영상/이미지 업로드, 변환, 최적화 서비스입니다.

주요 기능:
- 영상/이미지 업로드 및 관리
- 플랫폼별 영상 변환 (YouTube, Instagram, TikTok)
- 자동 썸네일 생성
- 최적화된 URL 생성
- 비용 추적 (Cloudinary는 월간 변환 횟수 기반)

Cloudinary 무료 Tier:
- 월 25,000회 변환
- 25GB 저장공간
- 25GB 대역폭
"""

from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import uuid
import httpx
from contextlib import nullcontext

import cloudinary
import cloudinary.uploader
import cloudinary.utils
import cloudinary.api

from app.core.config import get_settings
from app.services.cost_tracker import get_cost_tracker, APIProvider, APIService

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = (
        settings.LOGFIRE_TOKEN and
        settings.LOGFIRE_TOKEN != "your_logfire_token_here"
    )
except Exception:
    LOGFIRE_AVAILABLE = False


# 플랫폼별 영상 변환 설정
PLATFORM_TRANSFORMATIONS = {
    "youtube": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "crop": "fill",
        "quality": "auto:best",
        "format": "mp4",
        "audio_codec": "aac",
        "video_codec": "h264"
    },
    "instagram_feed": {
        "width": 1080,
        "height": 1080,
        "aspect_ratio": "1:1",
        "crop": "fill",
        "quality": "auto:good",
        "format": "mp4"
    },
    "instagram_story": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "crop": "fill",
        "quality": "auto:good",
        "format": "mp4"
    },
    "instagram_reels": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "crop": "fill",
        "quality": "auto:good",
        "format": "mp4"
    },
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "crop": "fill",
        "quality": "auto:good",
        "format": "mp4"
    },
    "facebook": {
        "width": 1280,
        "height": 720,
        "aspect_ratio": "16:9",
        "crop": "fill",
        "quality": "auto:good",
        "format": "mp4"
    }
}


class CloudinaryService:
    """Cloudinary 미디어 최적화 서비스"""

    def __init__(self, output_dir: str = "./outputs/cloudinary"):
        """
        Cloudinary 서비스 초기화

        Args:
            output_dir: 다운로드한 파일 저장 경로
        """
        # Cloudinary 초기화
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cost_tracker = get_cost_tracker()
        self.logger = logging.getLogger(__name__)

        # 변환 횟수 추적 (월간 무료 tier: 25,000회)
        self._transformation_count = 0

        self.logger.info("CloudinaryService initialized")

    async def upload_video(
        self,
        video_path: str,
        public_id: Optional[str] = None,
        folder: str = "videos",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        eager_transformations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        영상 업로드

        Args:
            video_path: 업로드할 영상 파일 경로
            public_id: Cloudinary public ID (없으면 자동 생성)
            folder: 저장할 폴더명
            user_id: 사용자 ID (비용 추적용)
            project_id: 프로젝트 ID (비용 추적용)
            eager_transformations: 즉시 적용할 변환 목록

        Returns:
            업로드 결과 딕셔너리
        """
        span_context = (
            logfire.span("cloudinary.upload_video")
            if LOGFIRE_AVAILABLE else nullcontext()
        )

        async with span_context:
            try:
                # public_id 생성 (없으면)
                if public_id is None:
                    public_id = self._generate_public_id("video")

                # eager transformations 기본값
                if eager_transformations is None:
                    eager_transformations = [
                        {
                            "width": 1920,
                            "height": 1080,
                            "crop": "limit",
                            "quality": "auto"
                        }
                    ]

                self.logger.info(f"Uploading video: {video_path} -> {folder}/{public_id}")

                # Cloudinary 업로드 (동기 함수를 비동기로 래핑)
                result = await self._async_upload(
                    video_path,
                    public_id=public_id,
                    folder=folder,
                    resource_type="video",
                    eager=eager_transformations,
                    eager_async=True,  # 비동기 변환
                    overwrite=True,
                    invalidate=True,
                    tags=["omnivibe", project_id] if project_id else ["omnivibe"]
                )

                # 비용 추적 (변환 1회)
                self._track_transformation_cost(
                    count=1,
                    user_id=user_id,
                    project_id=project_id,
                    metadata={
                        "operation": "upload_video",
                        "public_id": result["public_id"],
                        "bytes": result.get("bytes")
                    }
                )

                self.logger.info(
                    f"Video uploaded: {result['public_id']} "
                    f"({result.get('bytes', 0) / 1024 / 1024:.2f} MB)"
                )

                return {
                    "public_id": result["public_id"],
                    "url": result["url"],
                    "secure_url": result["secure_url"],
                    "format": result["format"],
                    "duration": result.get("duration"),
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "bytes": result["bytes"],
                    "created_at": result["created_at"]
                }

            except Exception as e:
                self.logger.error(f"Cloudinary video upload failed: {e}")
                raise

    async def upload_image(
        self,
        image_path: str,
        public_id: Optional[str] = None,
        folder: str = "images",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        transformations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        이미지 업로드

        Args:
            image_path: 업로드할 이미지 파일 경로
            public_id: Cloudinary public ID (없으면 자동 생성)
            folder: 저장할 폴더명
            user_id: 사용자 ID (비용 추적용)
            project_id: 프로젝트 ID (비용 추적용)
            transformations: 즉시 적용할 변환 목록

        Returns:
            업로드 결과 딕셔너리
        """
        span_context = (
            logfire.span("cloudinary.upload_image")
            if LOGFIRE_AVAILABLE else nullcontext()
        )

        async with span_context:
            try:
                # public_id 생성 (없으면)
                if public_id is None:
                    public_id = self._generate_public_id("image")

                # 기본 transformations
                if transformations is None:
                    transformations = [
                        {
                            "quality": "auto",
                            "fetch_format": "auto"
                        }
                    ]

                self.logger.info(f"Uploading image: {image_path} -> {folder}/{public_id}")

                # Cloudinary 업로드
                result = await self._async_upload(
                    image_path,
                    public_id=public_id,
                    folder=folder,
                    resource_type="image",
                    eager=transformations,
                    overwrite=True,
                    invalidate=True,
                    tags=["omnivibe", project_id] if project_id else ["omnivibe"]
                )

                # 비용 추적
                self._track_transformation_cost(
                    count=1,
                    user_id=user_id,
                    project_id=project_id,
                    metadata={
                        "operation": "upload_image",
                        "public_id": result["public_id"],
                        "bytes": result.get("bytes")
                    }
                )

                self.logger.info(f"Image uploaded: {result['public_id']}")

                return {
                    "public_id": result["public_id"],
                    "url": result["url"],
                    "secure_url": result["secure_url"],
                    "format": result["format"],
                    "width": result.get("width"),
                    "height": result.get("height"),
                    "bytes": result["bytes"],
                    "created_at": result["created_at"]
                }

            except Exception as e:
                self.logger.error(f"Cloudinary image upload failed: {e}")
                raise

    async def transform_video_for_platform(
        self,
        public_id: str,
        platform: str,
        output_path: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        플랫폼별 영상 변환 및 다운로드

        Args:
            public_id: Cloudinary public ID
            platform: 플랫폼명 (youtube, instagram_feed, instagram_story, tiktok, facebook)
            output_path: 저장할 파일 경로 (없으면 자동 생성)
            user_id: 사용자 ID (비용 추적용)
            project_id: 프로젝트 ID (비용 추적용)

        Returns:
            저장된 파일 경로
        """
        span_context = (
            logfire.span("cloudinary.transform_video")
            if LOGFIRE_AVAILABLE else nullcontext()
        )

        async with span_context:
            try:
                # 플랫폼 설정 가져오기
                if platform not in PLATFORM_TRANSFORMATIONS:
                    raise ValueError(
                        f"Unknown platform: {platform}. "
                        f"Supported: {list(PLATFORM_TRANSFORMATIONS.keys())}"
                    )

                config = PLATFORM_TRANSFORMATIONS[platform]

                self.logger.info(
                    f"Transforming video for {platform}: {public_id} "
                    f"({config['width']}x{config['height']})"
                )

                # Cloudinary 변환 URL 생성
                transformations = [
                    {
                        "width": config["width"],
                        "height": config["height"],
                        "crop": config["crop"],
                        "aspect_ratio": config["aspect_ratio"]
                    },
                    {
                        "quality": config["quality"]
                    },
                    {
                        "fetch_format": config["format"]
                    }
                ]

                # 오디오/비디오 코덱 설정 (있으면)
                if "audio_codec" in config:
                    transformations[0]["audio_codec"] = config["audio_codec"]
                if "video_codec" in config:
                    transformations[0]["video_codec"] = config["video_codec"]

                # URL 생성
                url, _ = cloudinary.utils.cloudinary_url(
                    public_id,
                    resource_type="video",
                    transformation=transformations,
                    secure=True
                )

                self.logger.info(f"Cloudinary URL: {url}")

                # 파일 다운로드
                if output_path is None:
                    output_path = str(
                        self.output_dir / f"{platform}_{public_id.replace('/', '_')}.{config['format']}"
                    )

                await self._download_file(url, output_path)

                # 비용 추적 (변환 1회)
                self._track_transformation_cost(
                    count=1,
                    user_id=user_id,
                    project_id=project_id,
                    metadata={
                        "operation": "transform_video",
                        "platform": platform,
                        "public_id": public_id,
                        "resolution": f"{config['width']}x{config['height']}"
                    }
                )

                self.logger.info(f"Video transformed and saved: {output_path}")
                return output_path

            except Exception as e:
                self.logger.error(f"Cloudinary video transformation failed: {e}")
                raise

    async def generate_thumbnail(
        self,
        video_public_id: str,
        time_offset: float = 0.0,
        width: int = 1280,
        height: int = 720,
        output_path: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        영상에서 썸네일 생성

        Args:
            video_public_id: Cloudinary 영상 public ID
            time_offset: 썸네일 추출 시간 (초)
            width: 썸네일 너비
            height: 썸네일 높이
            output_path: 저장할 파일 경로 (없으면 자동 생성)
            user_id: 사용자 ID (비용 추적용)
            project_id: 프로젝트 ID (비용 추적용)

        Returns:
            썸네일 URL
        """
        span_context = (
            logfire.span("cloudinary.generate_thumbnail")
            if LOGFIRE_AVAILABLE else nullcontext()
        )

        async with span_context:
            try:
                self.logger.info(
                    f"Generating thumbnail from {video_public_id} "
                    f"at {time_offset}s ({width}x{height})"
                )

                # Cloudinary 썸네일 생성
                transformations = [
                    {
                        "start_offset": f"{time_offset}s"
                    },
                    {
                        "width": width,
                        "height": height,
                        "crop": "fill"
                    },
                    {
                        "quality": "auto:best"
                    }
                ]

                url, _ = cloudinary.utils.cloudinary_url(
                    video_public_id,
                    resource_type="video",
                    format="jpg",
                    transformation=transformations,
                    secure=True
                )

                # 다운로드 (경로가 제공된 경우)
                if output_path:
                    await self._download_file(url, output_path)
                    self.logger.info(f"Thumbnail saved: {output_path}")

                # 비용 추적
                self._track_transformation_cost(
                    count=1,
                    user_id=user_id,
                    project_id=project_id,
                    metadata={
                        "operation": "generate_thumbnail",
                        "video_public_id": video_public_id,
                        "time_offset": time_offset,
                        "resolution": f"{width}x{height}"
                    }
                )

                return url

            except Exception as e:
                self.logger.error(f"Cloudinary thumbnail generation failed: {e}")
                raise

    async def optimize_image_for_platform(
        self,
        public_id: str,
        platform: str,
        output_path: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        플랫폼별 이미지 최적화

        Args:
            public_id: Cloudinary public ID
            platform: 플랫폼명
            output_path: 저장할 파일 경로
            user_id: 사용자 ID
            project_id: 프로젝트 ID

        Returns:
            최적화된 이미지 URL
        """
        try:
            # 플랫폼별 이미지 설정
            image_configs = {
                "youtube": {"width": 1280, "height": 720, "aspect_ratio": "16:9"},
                "instagram": {"width": 1080, "height": 1080, "aspect_ratio": "1:1"},
                "tiktok": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
                "facebook": {"width": 1200, "height": 630, "aspect_ratio": "1.91:1"}
            }

            if platform not in image_configs:
                raise ValueError(f"Unknown platform: {platform}")

            config = image_configs[platform]

            # 이미지 변환
            transformations = [
                {
                    "width": config["width"],
                    "height": config["height"],
                    "crop": "fill",
                    "aspect_ratio": config["aspect_ratio"]
                },
                {
                    "quality": "auto:best"
                },
                {
                    "fetch_format": "auto"
                }
            ]

            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type="image",
                transformation=transformations,
                secure=True
            )

            # 다운로드
            if output_path:
                await self._download_file(url, output_path)

            # 비용 추적
            self._track_transformation_cost(
                count=1,
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "operation": "optimize_image",
                    "platform": platform,
                    "public_id": public_id
                }
            )

            return url

        except Exception as e:
            self.logger.error(f"Image optimization failed: {e}")
            raise

    def get_optimized_url(
        self,
        public_id: str,
        resource_type: str = "image",
        transformations: Optional[List[Dict[str, Any]]] = None,
        format: Optional[str] = None
    ) -> str:
        """
        최적화된 URL 생성

        Args:
            public_id: Cloudinary public ID
            resource_type: 리소스 타입 (image, video)
            transformations: 적용할 변환 목록
            format: 파일 포맷

        Returns:
            최적화된 URL
        """
        try:
            # 기본 transformations (다양한 기기에서 최적 품질)
            if transformations is None:
                transformations = [
                    {
                        "quality": "auto:eco"
                    },
                    {
                        "fetch_format": "auto"
                    }
                ]

            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                transformation=transformations,
                format=format,
                secure=True
            )

            return url

        except Exception as e:
            self.logger.error(f"Failed to generate optimized URL: {e}")
            raise

    async def delete_asset(
        self,
        public_id: str,
        resource_type: str = "video"
    ) -> bool:
        """
        에셋 삭제

        Args:
            public_id: Cloudinary public ID
            resource_type: 리소스 타입 (image, video)

        Returns:
            삭제 성공 여부
        """
        try:
            self.logger.info(f"Deleting {resource_type}: {public_id}")

            # Cloudinary 삭제
            result = await self._async_destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True
            )

            success = result.get("result") == "ok"

            if success:
                self.logger.info(f"Asset deleted: {public_id}")
            else:
                self.logger.warning(f"Failed to delete asset: {public_id}")

            return success

        except Exception as e:
            self.logger.error(f"Cloudinary asset deletion failed: {e}")
            return False

    async def get_asset_info(
        self,
        public_id: str,
        resource_type: str = "video"
    ) -> Dict[str, Any]:
        """
        에셋 정보 조회

        Args:
            public_id: Cloudinary public ID
            resource_type: 리소스 타입

        Returns:
            에셋 정보
        """
        try:
            result = await self._async_resource(
                public_id,
                resource_type=resource_type
            )

            return {
                "public_id": result["public_id"],
                "format": result["format"],
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result["bytes"],
                "duration": result.get("duration"),
                "created_at": result["created_at"],
                "url": result["url"],
                "secure_url": result["secure_url"]
            }

        except Exception as e:
            self.logger.error(f"Failed to get asset info: {e}")
            raise

    # ========== Private Methods ==========

    def _generate_public_id(self, prefix: str = "media") -> str:
        """Public ID 생성"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    async def _async_upload(self, *args, **kwargs):
        """비동기 업로드 래퍼"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(*args, **kwargs)
        )

    async def _async_destroy(self, *args, **kwargs):
        """비동기 삭제 래퍼"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.destroy(*args, **kwargs)
        )

    async def _async_resource(self, *args, **kwargs):
        """비동기 리소스 조회 래퍼"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: cloudinary.api.resource(*args, **kwargs)
        )

    async def _download_file(self, url: str, output_path: str):
        """파일 다운로드"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=120.0)
                response.raise_for_status()

                # 파일 저장
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, "wb") as f:
                    f.write(response.content)

                self.logger.info(
                    f"Downloaded {len(response.content) / 1024 / 1024:.2f} MB to {output_path}"
                )

        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            raise

    def _track_transformation_cost(
        self,
        count: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        변환 비용 추적

        Cloudinary 무료 Tier: 월 25,000회 변환
        초과 시: $0.10 / 1,000 변환
        """
        try:
            self._transformation_count += count

            # CostTracker에 기록
            self.cost_tracker.record_cloudinary_usage(
                transformation_count=count,
                user_id=user_id,
                project_id=project_id,
                metadata=metadata
            )

            # 무료 tier 경고
            if self._transformation_count > 25000:
                self.logger.warning(
                    f"Cloudinary FREE tier exceeded: {self._transformation_count} transformations"
                )

        except Exception as e:
            self.logger.warning(f"Failed to track Cloudinary cost: {e}")


# 싱글톤 인스턴스
_cloudinary_service_instance: Optional[CloudinaryService] = None


def get_cloudinary_service() -> CloudinaryService:
    """CloudinaryService 싱글톤 인스턴스 반환"""
    global _cloudinary_service_instance

    if _cloudinary_service_instance is None:
        _cloudinary_service_instance = CloudinaryService()

    return _cloudinary_service_instance
