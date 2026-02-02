"""플랫폼 프리셋 서비스

플랫폼별 영상 스타일 프리셋 관리 및 적용
"""
from typing import Dict, Any, Optional, List
import logging

from app.constants.platform_presets import (
    PLATFORM_PRESETS,
    get_preset,
    get_all_platforms
)
from app.services.neo4j_client import Neo4jClient
from app.models.neo4j_models import Neo4jCRUDManager

logger = logging.getLogger(__name__)


class PresetService:
    """플랫폼 프리셋 서비스"""

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client
        self.crud = Neo4jCRUDManager(neo4j_client)

    def get_all_platform_presets(self) -> List[Dict[str, Any]]:
        """
        모든 플랫폼 프리셋 목록 조회

        Returns:
            플랫폼 프리셋 리스트
        """
        try:
            platforms = get_all_platforms()
            presets = []

            for platform in platforms:
                preset = PLATFORM_PRESETS[platform]
                # 간략 정보만 반환
                presets.append({
                    "platform": preset["platform"],
                    "name": preset["name"],
                    "description": preset["description"],
                    "aspect_ratio": preset["aspect_ratio"],
                    "resolution": preset["resolution"],
                    "max_duration": preset["max_duration"]
                })

            logger.info(f"Retrieved {len(presets)} platform presets")
            return presets

        except Exception as e:
            logger.error(f"Failed to get platform presets: {e}")
            raise

    def get_platform_preset(self, platform: str) -> Dict[str, Any]:
        """
        특정 플랫폼 프리셋 상세 조회

        Args:
            platform: 플랫폼 이름 (youtube, instagram, tiktok, facebook)

        Returns:
            플랫폼 프리셋 전체 정보

        Raises:
            ValueError: 지원하지 않는 플랫폼
        """
        try:
            preset = get_preset(platform)
            logger.info(f"Retrieved preset for platform: {platform}")
            return preset

        except ValueError as e:
            logger.warning(f"Invalid platform requested: {platform}")
            raise
        except Exception as e:
            logger.error(f"Failed to get preset for {platform}: {e}")
            raise

    def apply_preset_to_project(
        self,
        project_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        프로젝트에 플랫폼 프리셋 적용

        Args:
            project_id: 프로젝트 ID
            platform: 플랫폼 이름

        Returns:
            적용된 프리셋 정보

        Raises:
            ValueError: 유효하지 않은 플랫폼
            Exception: 프로젝트를 찾을 수 없거나 적용 실패
        """
        try:
            # 1. 프리셋 가져오기
            preset = get_preset(platform)

            # 2. 프로젝트 존재 확인
            project = self.crud.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # 3. Neo4j에 프리셋 적용 기록
            application = self.crud.apply_platform_preset_to_project(
                project_id=project_id,
                platform=platform,
                preset_settings=preset
            )

            if not application:
                raise Exception("Failed to apply preset to project")

            logger.info(
                f"Applied {platform} preset to project {project_id}. "
                f"Application ID: {application.get('application_id')}"
            )

            return {
                "project_id": project_id,
                "platform": platform,
                "preset": preset,
                "applied_at": application.get("applied_at"),
                "application_id": application.get("application_id")
            }

        except ValueError as e:
            logger.warning(f"Invalid input for apply_preset_to_project: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to apply preset to project {project_id}: {e}")
            raise

    def get_project_current_preset(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        프로젝트에 현재 적용된 프리셋 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            현재 적용된 프리셋 정보 (없으면 None)
        """
        try:
            preset_application = self.crud.get_project_platform_preset(project_id)

            if not preset_application:
                logger.info(f"No preset applied to project: {project_id}")
                return None

            logger.info(
                f"Retrieved current preset for project {project_id}: "
                f"{preset_application.get('platform')}"
            )

            return preset_application

        except Exception as e:
            logger.error(f"Failed to get current preset for project {project_id}: {e}")
            raise

    def get_project_preset_history(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 프리셋 적용 이력 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            프리셋 적용 이력 리스트 (최신순)
        """
        try:
            history = self.crud.get_project_preset_history(project_id)

            logger.info(
                f"Retrieved preset history for project {project_id}: "
                f"{len(history)} applications"
            )

            return history

        except Exception as e:
            logger.error(f"Failed to get preset history for project {project_id}: {e}")
            raise

    def validate_preset_compatibility(
        self,
        project_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        프로젝트와 프리셋 호환성 검증

        Args:
            project_id: 프로젝트 ID
            platform: 플랫폼 이름

        Returns:
            호환성 검증 결과
        """
        try:
            # 프로젝트 조회
            project = self.crud.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # 프리셋 조회
            preset = get_preset(platform)

            # 검증 로직
            warnings = []

            # 1. 플랫폼 일치 여부 확인
            if project.get("platform") != platform:
                warnings.append(
                    f"Project platform ({project.get('platform')}) differs "
                    f"from preset platform ({platform})"
                )

            # 2. 프로젝트에 스크립트가 있는지 확인
            scripts = self.crud.get_project_scripts(project_id)
            if scripts:
                # 스크립트의 예상 길이와 프리셋 최대 길이 비교
                for script in scripts:
                    estimated_duration = script.get("estimated_duration", 0)
                    max_duration = preset.get("max_duration", 180)

                    if estimated_duration > max_duration:
                        warnings.append(
                            f"Script duration ({estimated_duration}s) exceeds "
                            f"platform max duration ({max_duration}s)"
                        )

            is_compatible = len(warnings) == 0

            result = {
                "compatible": is_compatible,
                "warnings": warnings,
                "project_platform": project.get("platform"),
                "preset_platform": platform,
                "preset_max_duration": preset.get("max_duration")
            }

            logger.info(
                f"Compatibility check for project {project_id} with {platform} preset: "
                f"{'Compatible' if is_compatible else 'Has warnings'}"
            )

            return result

        except ValueError as e:
            logger.warning(f"Invalid input for validate_preset_compatibility: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Failed to validate compatibility for project {project_id}: {e}"
            )
            raise


def get_preset_service(neo4j_client: Neo4jClient) -> PresetService:
    """PresetService 싱글톤 팩토리"""
    return PresetService(neo4j_client)
