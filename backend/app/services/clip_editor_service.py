"""클립 에디터 서비스

섹션별 대체 클립 생성 및 관리 서비스

주요 기능:
- AI 기반 대체 클립 3개 자동 생성 (카메라 앵글, 조명, 색감 변형)
- Google Veo API를 활용한 영상 생성
- Cloudinary를 통한 썸네일 생성 및 최적화
- Neo4j에 클립 메타데이터 저장
- 원클릭 클립 교체
"""

from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from pathlib import Path
from contextlib import nullcontext

from app.core.config import get_settings
from app.services.veo_service import get_veo_service, VeoService
from app.services.cloudinary_service import get_cloudinary_service, CloudinaryService
from app.services.neo4j_client import get_neo4j_client, Neo4jClient
from app.models.neo4j_models import (
    AlternativeClipModel,
    ClipVariationType,
    Neo4jCRUDManager
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class PromptVariationGenerator:
    """프롬프트 변형 생성기"""

    # 카메라 앵글 변형
    CAMERA_ANGLES = {
        "close_up": "Close-up shot, tight framing on subject",
        "medium_shot": "Medium shot, waist-up view of subject",
        "wide_shot": "Wide shot, full body view with environment"
    }

    # 조명 스타일 변형
    LIGHTING_STYLES = {
        "natural": "Natural lighting, soft daylight, realistic shadows",
        "dramatic": "Dramatic lighting, high contrast, cinematic mood lighting",
        "soft": "Soft lighting, diffused light, gentle shadows, bright and airy"
    }

    # 색감 변형
    COLOR_TONES = {
        "warm": "Warm color grading, golden hour tones, orange and yellow hues",
        "cool": "Cool color grading, blue and teal tones, modern aesthetic",
        "neutral": "Neutral color grading, balanced tones, natural colors"
    }

    @classmethod
    def generate_camera_angle_variation(cls, base_prompt: str) -> List[Dict[str, str]]:
        """카메라 앵글 변형 생성"""
        variations = []
        for angle_key, angle_desc in cls.CAMERA_ANGLES.items():
            variations.append({
                "type": "camera_angle",
                "variation_key": angle_key,
                "prompt": f"{base_prompt}. {angle_desc}",
                "description": angle_desc
            })
        return variations

    @classmethod
    def generate_lighting_variation(cls, base_prompt: str) -> List[Dict[str, str]]:
        """조명 스타일 변형 생성"""
        variations = []
        for lighting_key, lighting_desc in cls.LIGHTING_STYLES.items():
            variations.append({
                "type": "lighting",
                "variation_key": lighting_key,
                "prompt": f"{base_prompt}. {lighting_desc}",
                "description": lighting_desc
            })
        return variations

    @classmethod
    def generate_color_tone_variation(cls, base_prompt: str) -> List[Dict[str, str]]:
        """색감 변형 생성"""
        variations = []
        for tone_key, tone_desc in cls.COLOR_TONES.items():
            variations.append({
                "type": "color_tone",
                "variation_key": tone_key,
                "prompt": f"{base_prompt}. {tone_desc}",
                "description": tone_desc
            })
        return variations

    @classmethod
    def generate_all_variations(cls, base_prompt: str) -> Dict[str, List[Dict[str, str]]]:
        """모든 변형 생성"""
        return {
            "camera_angle": cls.generate_camera_angle_variation(base_prompt),
            "lighting": cls.generate_lighting_variation(base_prompt),
            "color_tone": cls.generate_color_tone_variation(base_prompt)
        }

    @classmethod
    def get_variation_by_type(
        cls,
        base_prompt: str,
        variation_type: str,
        variation_key: Optional[str] = None
    ) -> Dict[str, str]:
        """특정 타입의 변형 1개 반환"""
        all_variations = cls.generate_all_variations(base_prompt)

        if variation_type not in all_variations:
            raise ValueError(f"Unknown variation type: {variation_type}")

        variations = all_variations[variation_type]

        if variation_key:
            # 특정 키의 변형 반환
            for var in variations:
                if var["variation_key"] == variation_key:
                    return var
            raise ValueError(f"Unknown variation key: {variation_key} for type: {variation_type}")
        else:
            # 첫 번째 변형 반환
            return variations[0]


class ClipEditorService:
    """클립 에디터 서비스"""

    def __init__(
        self,
        veo_service: Optional[VeoService] = None,
        cloudinary_service: Optional[CloudinaryService] = None,
        neo4j_client: Optional[Neo4jClient] = None,
        output_dir: str = "./outputs/alternative_clips"
    ):
        """
        Args:
            veo_service: VeoService 인스턴스
            cloudinary_service: CloudinaryService 인스턴스
            neo4j_client: Neo4jClient 인스턴스
            output_dir: 클립 저장 경로
        """
        self.veo_service = veo_service or get_veo_service()
        self.cloudinary_service = cloudinary_service or get_cloudinary_service()
        self.neo4j_client = neo4j_client or get_neo4j_client()
        self.crud = Neo4jCRUDManager(self.neo4j_client)

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

    async def generate_alternative_clips(
        self,
        section_id: str,
        base_prompt: Optional[str] = None,
        variation_types: Optional[List[str]] = None,
        duration: int = 5,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        대체 클립 3개 생성 (비동기 병렬)

        Args:
            section_id: 섹션 ID
            base_prompt: 기본 프롬프트 (없으면 섹션 정보에서 생성)
            variation_types: 변형 타입 목록 (기본: camera_angle, lighting, color_tone)
            duration: 영상 길이 (초)
            user_id: 사용자 ID
            project_id: 프로젝트 ID

        Returns:
            생성된 클립 정보 리스트
        """
        span_context = logfire.span("clip_editor.generate_alternative_clips") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context:
            try:
                # 1. 기본 프롬프트 생성 (없으면)
                if not base_prompt:
                    base_prompt = await self._get_section_prompt(section_id)

                # 2. 변형 타입 기본값
                if not variation_types:
                    variation_types = ["camera_angle", "lighting", "color_tone"]

                self.logger.info(
                    f"Generating {len(variation_types)} alternative clips for section {section_id}"
                )

                # 3. 각 변형 타입별로 클립 생성
                clip_results = []

                for i, variation_type in enumerate(variation_types):
                    # 변형 프롬프트 생성
                    variation = PromptVariationGenerator.get_variation_by_type(
                        base_prompt,
                        variation_type
                    )

                    # AlternativeClipModel 생성
                    clip_model = AlternativeClipModel(
                        prompt=variation["prompt"],
                        variation_type=ClipVariationType(variation_type),
                        variation_description=variation["description"],
                        status="generating"
                    )

                    # Neo4j에 저장 (상태: generating)
                    created_clip = self.crud.create_alternative_clip(section_id, clip_model)

                    # Veo API 호출 (비동기)
                    veo_result = await self.veo_service.generate_video(
                        prompt=variation["prompt"],
                        duration=duration,
                        style="commercial",
                        aspect_ratio="16:9"
                    )

                    # veo_job_id 업데이트
                    if veo_result.get("job_id"):
                        self.crud.update_alternative_clip_status(
                            clip_model.clip_id,
                            status="processing",
                            video_path="",
                            thumbnail_url=""
                        )

                    clip_results.append({
                        "clip_id": clip_model.clip_id,
                        "variation_type": variation_type,
                        "variation_description": variation["description"],
                        "prompt": variation["prompt"],
                        "veo_job_id": veo_result.get("job_id"),
                        "status": "processing",
                        "estimated_time": veo_result.get("estimated_time")
                    })

                    self.logger.info(
                        f"Alternative clip {i+1}/{len(variation_types)} created: "
                        f"{variation_type} ({clip_model.clip_id})"
                    )

                self.logger.info(f"All {len(clip_results)} alternative clips initiated")

                return clip_results

            except Exception as e:
                self.logger.error(f"Failed to generate alternative clips: {e}", exc_info=True)
                raise

    async def get_section_alternative_clips(
        self,
        section_id: str
    ) -> Dict[str, Any]:
        """
        섹션의 현재 클립 및 대체 클립 목록 조회

        Args:
            section_id: 섹션 ID

        Returns:
            {
                "section_id": str,
                "current_clip": {...},
                "alternatives": [...]
            }
        """
        try:
            # 현재 클립 조회
            current_clip_data = self.crud.get_section_current_clip(section_id)
            current_clip = None

            if current_clip_data and current_clip_data.get("clip_id"):
                current_clip = {
                    "clip_id": current_clip_data["clip_id"],
                    "video_path": current_clip_data.get("video_path", ""),
                    "thumbnail_url": current_clip_data.get("thumbnail_url", ""),
                    "prompt": current_clip_data.get("prompt", ""),
                    "created_at": current_clip_data.get("created_at", "")
                }

            # 대체 클립 목록 조회
            alternative_clips = self.crud.get_section_alternative_clips(section_id)

            alternatives = []
            for clip in alternative_clips:
                alternatives.append({
                    "clip_id": clip["clip_id"],
                    "video_path": clip.get("video_path", ""),
                    "thumbnail_url": clip.get("thumbnail_url", ""),
                    "prompt": clip.get("prompt", ""),
                    "variation": clip.get("variation_type", ""),
                    "created_at": clip.get("created_at", "")
                })

            return {
                "section_id": section_id,
                "current_clip": current_clip,
                "alternatives": alternatives
            }

        except Exception as e:
            self.logger.error(f"Failed to get alternative clips: {e}", exc_info=True)
            raise

    async def replace_section_clip(
        self,
        section_id: str,
        new_clip_id: str
    ) -> bool:
        """
        섹션의 클립 교체

        Args:
            section_id: 섹션 ID
            new_clip_id: 새 클립 ID

        Returns:
            교체 성공 여부
        """
        try:
            self.logger.info(f"Replacing clip for section {section_id} with {new_clip_id}")

            success = self.crud.replace_section_clip(section_id, new_clip_id)

            if success:
                self.logger.info(f"Clip replaced successfully: {section_id} -> {new_clip_id}")
            else:
                self.logger.warning(f"Failed to replace clip: {section_id}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to replace clip: {e}", exc_info=True)
            raise

    async def delete_alternative_clip(
        self,
        clip_id: str,
        delete_from_cloudinary: bool = True
    ) -> bool:
        """
        대체 클립 삭제

        Args:
            clip_id: 클립 ID
            delete_from_cloudinary: Cloudinary에서도 삭제 여부

        Returns:
            삭제 성공 여부
        """
        try:
            self.logger.info(f"Deleting alternative clip: {clip_id}")

            # Cloudinary에서 삭제 (옵션)
            if delete_from_cloudinary:
                # TODO: Cloudinary public_id 조회 및 삭제
                pass

            # Neo4j에서 삭제
            success = self.crud.delete_alternative_clip(clip_id)

            if success:
                self.logger.info(f"Alternative clip deleted: {clip_id}")
            else:
                self.logger.warning(f"Failed to delete clip: {clip_id}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to delete alternative clip: {e}", exc_info=True)
            raise

    async def check_and_update_clip_status(
        self,
        clip_id: str
    ) -> Dict[str, Any]:
        """
        클립 생성 상태 확인 및 업데이트

        Args:
            clip_id: 클립 ID

        Returns:
            업데이트된 클립 정보
        """
        try:
            # TODO: Veo job_id로 상태 확인 및 다운로드
            # TODO: Cloudinary 업로드 및 썸네일 생성
            # TODO: Neo4j 상태 업데이트

            self.logger.info(f"Checking clip status: {clip_id}")

            return {
                "clip_id": clip_id,
                "status": "processing",
                "message": "Status check not implemented yet"
            }

        except Exception as e:
            self.logger.error(f"Failed to check clip status: {e}", exc_info=True)
            raise

    # ==================== Private Methods ====================

    async def _get_section_prompt(self, section_id: str) -> str:
        """섹션 정보에서 기본 프롬프트 생성"""
        # TODO: Neo4j에서 섹션 정보 조회 및 프롬프트 생성
        return "Modern studio setting, friendly presenter, professional lighting, shallow depth of field"

    async def _generate_thumbnail_from_video(
        self,
        video_path: str,
        time_offset: float = 1.0
    ) -> str:
        """영상에서 썸네일 추출"""
        try:
            # Cloudinary 업로드 및 썸네일 생성
            # TODO: 구현
            return ""
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {e}")
            return ""


# ==================== 싱글톤 인스턴스 ====================

_clip_editor_service: Optional[ClipEditorService] = None


def get_clip_editor_service() -> ClipEditorService:
    """
    ClipEditorService 싱글톤 인스턴스

    Returns:
        ClipEditorService 인스턴스
    """
    global _clip_editor_service
    if _clip_editor_service is None:
        _clip_editor_service = ClipEditorService()
    return _clip_editor_service
