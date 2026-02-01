"""리소스 관리 서비스 - PDF, 이미지, 영상 처리

이 서비스는 콘티 생성에 사용되는 모든 리소스를 관리합니다:
- PDF → 이미지 변환
- 이미지 최적화 및 포맷 변환
- 영상 클립 자르기
- 클라우드 스토리지 업로드 (Cloudinary)
"""
from typing import Dict, Any, List, Optional, BinaryIO
import logging
from pathlib import Path
from datetime import datetime
import uuid
import io

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ResourceType:
    """리소스 타입"""
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    AUDIO = "audio"


class Resource:
    """리소스 모델"""
    def __init__(
        self,
        id: str,
        type: str,
        name: str,
        url: str,
        size_bytes: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.type = type
        self.name = name
        self.url = url
        self.size_bytes = size_bytes
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()


class ResourceManager:
    """리소스 관리 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.storage_dir = Path("./resources")
        self.storage_dir.mkdir(exist_ok=True)

        # Cloudinary 설정 (옵션)
        self.cloudinary_enabled = (
            settings.CLOUDINARY_CLOUD_NAME and
            settings.CLOUDINARY_CLOUD_NAME != "your_cloud_name"
        )

        if self.cloudinary_enabled:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET
                )
                self.logger.info("Cloudinary enabled")
            except Exception as e:
                self.logger.warning(f"Cloudinary initialization failed: {e}")
                self.cloudinary_enabled = False

    def detect_resource_type(self, filename: str) -> str:
        """파일명에서 리소스 타입 감지"""
        ext = Path(filename).suffix.lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            return ResourceType.IMAGE
        elif ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']:
            return ResourceType.VIDEO
        elif ext == '.pdf':
            return ResourceType.PDF
        elif ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']:
            return ResourceType.AUDIO
        else:
            return "unknown"

    async def upload_resource(
        self,
        file_data: bytes,
        filename: str,
        campaign_name: Optional[str] = None
    ) -> Resource:
        """
        리소스 업로드

        Args:
            file_data: 파일 바이너리 데이터
            filename: 원본 파일명
            campaign_name: 캠페인명 (폴더 구분용)

        Returns:
            Resource 객체
        """
        try:
            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            resource_type = self.detect_resource_type(filename)

            # 로컬 저장
            local_path = await self._save_local(
                file_data,
                filename,
                resource_id,
                campaign_name
            )

            # Cloudinary 업로드 (활성화된 경우)
            if self.cloudinary_enabled:
                url = await self._upload_cloudinary(
                    file_data,
                    filename,
                    resource_type,
                    resource_id
                )
            else:
                url = f"file://{local_path}"

            resource = Resource(
                id=resource_id,
                type=resource_type,
                name=filename,
                url=url,
                size_bytes=len(file_data),
                metadata={
                    "local_path": str(local_path),
                    "campaign_name": campaign_name
                }
            )

            self.logger.info(f"Resource uploaded: {resource_id} ({resource_type})")
            return resource

        except Exception as e:
            self.logger.error(f"Failed to upload resource: {e}")
            raise

    async def _save_local(
        self,
        file_data: bytes,
        filename: str,
        resource_id: str,
        campaign_name: Optional[str] = None
    ) -> Path:
        """로컬 저장"""
        # 캠페인별 디렉토리
        if campaign_name:
            safe_campaign = campaign_name.replace(" ", "_").replace("/", "_")[:50]
            campaign_dir = self.storage_dir / safe_campaign
            campaign_dir.mkdir(exist_ok=True)
        else:
            campaign_dir = self.storage_dir / "default"
            campaign_dir.mkdir(exist_ok=True)

        # 파일 저장
        ext = Path(filename).suffix
        local_path = campaign_dir / f"{resource_id}{ext}"

        with open(local_path, "wb") as f:
            f.write(file_data)

        return local_path

    async def _upload_cloudinary(
        self,
        file_data: bytes,
        filename: str,
        resource_type: str,
        resource_id: str
    ) -> str:
        """Cloudinary 업로드"""
        import cloudinary.uploader

        # 리소스 타입에 따라 Cloudinary 업로드 타입 결정
        if resource_type == ResourceType.VIDEO:
            upload_type = "video"
        elif resource_type == ResourceType.IMAGE or resource_type == ResourceType.PDF:
            upload_type = "image"
        else:
            upload_type = "raw"

        result = cloudinary.uploader.upload(
            io.BytesIO(file_data),
            resource_type=upload_type,
            public_id=resource_id,
            folder="omnivibe_resources"
        )

        return result["secure_url"]

    async def convert_pdf_to_images(
        self,
        pdf_data: bytes,
        campaign_name: Optional[str] = None
    ) -> List[Resource]:
        """
        PDF를 이미지로 변환

        Args:
            pdf_data: PDF 파일 데이터
            campaign_name: 캠페인명

        Returns:
            변환된 이미지 리소스 리스트
        """
        try:
            from pdf2image import convert_from_bytes

            # PDF → 이미지 변환
            images = convert_from_bytes(pdf_data, dpi=300)

            resources = []
            for idx, image in enumerate(images):
                # PIL Image → bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                # 리소스 업로드
                resource = await self.upload_resource(
                    file_data=img_bytes.read(),
                    filename=f"slide_{idx + 1}.png",
                    campaign_name=campaign_name
                )
                resources.append(resource)

            self.logger.info(f"Converted PDF to {len(resources)} images")
            return resources

        except ImportError:
            self.logger.error("pdf2image not installed. Install: pip install pdf2image poppler-utils")
            raise
        except Exception as e:
            self.logger.error(f"Failed to convert PDF: {e}")
            raise

    async def optimize_image(
        self,
        image_data: bytes,
        max_width: int = 1920,
        quality: int = 85
    ) -> bytes:
        """
        이미지 최적화

        Args:
            image_data: 원본 이미지 데이터
            max_width: 최대 너비
            quality: JPEG 품질 (1-100)

        Returns:
            최적화된 이미지 데이터
        """
        try:
            from PIL import Image

            # 이미지 로드
            image = Image.open(io.BytesIO(image_data))

            # 리사이즈 (비율 유지)
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # RGB 변환 (JPEG 호환)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # 저장
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            self.logger.info(f"Image optimized: {len(image_data)} → {len(output.getvalue())} bytes")
            return output.getvalue()

        except Exception as e:
            self.logger.error(f"Failed to optimize image: {e}")
            return image_data  # 실패 시 원본 반환

    async def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        영상 메타데이터 추출

        Args:
            video_path: 영상 파일 경로

        Returns:
            메타데이터 (duration, width, height, fps 등)
        """
        try:
            import ffmpeg

            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                return {}

            metadata = {
                "duration": float(probe['format']['duration']),
                "width": int(video_stream['width']),
                "height": int(video_stream['height']),
                "fps": eval(video_stream['r_frame_rate']),  # "30/1" → 30.0
                "codec": video_stream['codec_name']
            }

            return metadata

        except ImportError:
            self.logger.warning("ffmpeg-python not installed. Video metadata unavailable.")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to extract video metadata: {e}")
            return {}

    async def trim_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        영상 클립 자르기

        Args:
            video_path: 원본 영상 경로
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)
            output_path: 출력 경로 (옵션)

        Returns:
            잘린 영상 경로
        """
        try:
            import ffmpeg

            if not output_path:
                output_path = str(
                    self.storage_dir / f"trimmed_{uuid.uuid4().hex[:8]}.mp4"
                )

            # FFmpeg로 자르기
            (
                ffmpeg
                .input(video_path, ss=start_time, to=end_time)
                .output(output_path, codec='copy')
                .overwrite_output()
                .run(quiet=True)
            )

            self.logger.info(f"Video trimmed: {start_time}s - {end_time}s → {output_path}")
            return output_path

        except ImportError:
            self.logger.error("ffmpeg-python not installed")
            raise
        except Exception as e:
            self.logger.error(f"Failed to trim video: {e}")
            raise


# 싱글톤 인스턴스
_resource_manager_instance = None


def get_resource_manager() -> ResourceManager:
    """ResourceManager 싱글톤 인스턴스"""
    global _resource_manager_instance
    if _resource_manager_instance is None:
        _resource_manager_instance = ResourceManager()
    return _resource_manager_instance
