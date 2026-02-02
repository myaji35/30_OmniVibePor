"""커스텀 프리셋 & 플랫폼 프리셋 API 엔드포인트"""
from fastapi import APIRouter, HTTPException, status, Depends, Path, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.neo4j_models import (
    CustomPresetModel,
    CustomPresetCreateRequest,
    CustomPresetUpdateRequest,
    CustomPresetResponse,
    CustomPresetListResponse,
    Neo4jCRUDManager,
    SubtitleStyleModel,
    BGMSettingsModel,
    VideoSettingsModel,
    Platform
)
from app.services.neo4j_client import get_neo4j_client
from app.services.preset_service import get_preset_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/presets", tags=["presets"])
logger = logging.getLogger(__name__)


# ==================== Platform Preset Response Models ====================

class ResolutionResponse(BaseModel):
    """해상도 응답"""
    width: int
    height: int


class PlatformPresetSummary(BaseModel):
    """플랫폼 프리셋 요약 정보"""
    platform: str
    name: str
    description: str
    aspect_ratio: str
    resolution: ResolutionResponse
    max_duration: int


class PlatformPresetDetail(BaseModel):
    """플랫폼 프리셋 상세 정보"""
    platform: str
    name: str
    description: str
    resolution: ResolutionResponse
    aspect_ratio: str
    frame_rate: int
    bitrate: int
    subtitle_style: Dict[str, Any]
    bgm_settings: Dict[str, Any]
    transition_style: str
    transition_duration: float
    color_grading: str
    max_duration: int


class PlatformPresetApplicationRequest(BaseModel):
    """플랫폼 프리셋 적용 요청"""
    platform: Platform = Field(..., description="적용할 플랫폼 프리셋")


class PlatformPresetApplicationResponse(BaseModel):
    """플랫폼 프리셋 적용 응답"""
    project_id: str
    platform: str
    applied_at: datetime
    application_id: str
    preset: Dict[str, Any]


class PresetHistoryItem(BaseModel):
    """프리셋 적용 이력 항목"""
    application_id: str
    platform: str
    applied_at: datetime
    preset_settings: Dict[str, Any]


class PresetCompatibilityResponse(BaseModel):
    """프리셋 호환성 검증 응답"""
    compatible: bool
    warnings: List[str]
    project_platform: str
    preset_platform: str
    preset_max_duration: int


def get_crud_manager() -> Neo4jCRUDManager:
    """Neo4j CRUD Manager 의존성"""
    neo4j_client = get_neo4j_client()
    return Neo4jCRUDManager(neo4j_client)


@router.get("/custom", response_model=CustomPresetListResponse)
async def get_custom_presets(
    user_id: str,
    favorite_only: bool = False,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    사용자의 커스텀 프리셋 목록 조회

    **Parameters:**
    - `user_id`: 사용자 ID
    - `favorite_only`: 즐겨찾기만 조회 (기본값: False)

    **Returns:**
    - 프리셋 목록 및 총 개수
    """
    try:
        presets = crud_manager.get_user_custom_presets(
            user_id=user_id,
            favorite_only=favorite_only
        )

        preset_responses = [
            CustomPresetResponse(
                preset_id=p["preset_id"],
                user_id=user_id,
                name=p["name"],
                description=p.get("description"),
                subtitle_style=p["subtitle_style"],
                bgm_settings=p["bgm_settings"],
                video_settings=p["video_settings"],
                is_favorite=p["is_favorite"],
                usage_count=p["usage_count"],
                created_at=p["created_at"],
                updated_at=p["updated_at"]
            )
            for p in presets
        ]

        return CustomPresetListResponse(
            presets=preset_responses,
            total=len(preset_responses)
        )

    except Exception as e:
        logger.error(f"Failed to get custom presets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom presets: {str(e)}"
        )


@router.post("/custom", response_model=CustomPresetResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_preset(
    user_id: str,
    request: CustomPresetCreateRequest,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    커스텀 프리셋 생성

    **Parameters:**
    - `user_id`: 사용자 ID
    - `request`: 프리셋 생성 요청 데이터

    **Returns:**
    - 생성된 프리셋 정보
    """
    try:
        # 기본값 설정
        subtitle_style = request.subtitle_style or SubtitleStyleModel()
        bgm_settings = request.bgm_settings or BGMSettingsModel(
            bgm_file_path="",  # 필수 필드이므로 빈 문자열
        )
        video_settings = request.video_settings or VideoSettingsModel()

        # CustomPresetModel 생성
        preset = CustomPresetModel(
            user_id=user_id,
            name=request.name,
            description=request.description,
            subtitle_style=subtitle_style,
            bgm_settings=bgm_settings,
            video_settings=video_settings,
            is_favorite=request.is_favorite
        )

        # Neo4j에 저장
        result = crud_manager.create_custom_preset(
            user_id=user_id,
            preset=preset
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create custom preset"
            )

        return CustomPresetResponse(
            preset_id=result["preset_id"],
            user_id=user_id,
            name=result["name"],
            description=result.get("description"),
            subtitle_style=result["subtitle_style"],
            bgm_settings=result["bgm_settings"],
            video_settings=result["video_settings"],
            is_favorite=result["is_favorite"],
            usage_count=result["usage_count"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom preset: {str(e)}"
        )


@router.get("/custom/{preset_id}", response_model=CustomPresetResponse)
async def get_custom_preset_detail(
    preset_id: str,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    커스텀 프리셋 상세 조회

    **Parameters:**
    - `preset_id`: 프리셋 ID

    **Returns:**
    - 프리셋 상세 정보
    """
    try:
        preset = crud_manager.get_custom_preset(preset_id)

        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom preset {preset_id} not found"
            )

        return CustomPresetResponse(
            preset_id=preset["preset_id"],
            user_id=preset["user_id"],
            name=preset["name"],
            description=preset.get("description"),
            subtitle_style=preset["subtitle_style"],
            bgm_settings=preset["bgm_settings"],
            video_settings=preset["video_settings"],
            is_favorite=preset["is_favorite"],
            usage_count=preset["usage_count"],
            created_at=preset["created_at"],
            updated_at=preset["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom preset: {str(e)}"
        )


@router.patch("/custom/{preset_id}", response_model=dict)
async def update_custom_preset(
    preset_id: str,
    request: CustomPresetUpdateRequest,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    커스텀 프리셋 수정

    **Parameters:**
    - `preset_id`: 프리셋 ID
    - `request`: 프리셋 수정 요청 데이터

    **Returns:**
    - 수정 결과
    """
    try:
        # 프리셋 존재 확인
        preset = crud_manager.get_custom_preset(preset_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom preset {preset_id} not found"
            )

        # 업데이트할 필드만 추출
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.subtitle_style is not None:
            updates["subtitle_style"] = request.subtitle_style.model_dump()
        if request.bgm_settings is not None:
            updates["bgm_settings"] = request.bgm_settings.model_dump()
        if request.video_settings is not None:
            updates["video_settings"] = request.video_settings.model_dump()
        if request.is_favorite is not None:
            updates["is_favorite"] = request.is_favorite

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # 업데이트 실행
        success = crud_manager.update_custom_preset(preset_id, updates)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update custom preset"
            )

        return {
            "preset_id": preset_id,
            "message": "Custom preset updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update custom preset: {str(e)}"
        )


@router.delete("/custom/{preset_id}", response_model=dict)
async def delete_custom_preset(
    preset_id: str,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    커스텀 프리셋 삭제

    **Parameters:**
    - `preset_id`: 프리셋 ID

    **Returns:**
    - 삭제 결과
    """
    try:
        # 프리셋 존재 확인
        preset = crud_manager.get_custom_preset(preset_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom preset {preset_id} not found"
            )

        # 삭제 실행
        success = crud_manager.delete_custom_preset(preset_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete custom preset"
            )

        return {
            "preset_id": preset_id,
            "message": "Custom preset deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete custom preset: {str(e)}"
        )


@router.post("/custom/{preset_id}/apply", response_model=dict)
async def apply_custom_preset_to_project(
    preset_id: str,
    project_id: str,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    프로젝트에 커스텀 프리셋 적용

    **Parameters:**
    - `preset_id`: 프리셋 ID
    - `project_id`: 프로젝트 ID

    **Returns:**
    - 적용 결과
    """
    try:
        # 프리셋 존재 확인
        preset = crud_manager.get_custom_preset(preset_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom preset {preset_id} not found"
            )

        # 프로젝트 존재 확인
        project = crud_manager.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # 프리셋 적용
        success = crud_manager.apply_custom_preset_to_project(project_id, preset_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply custom preset"
            )

        return {
            "preset_id": preset_id,
            "project_id": project_id,
            "message": "Custom preset applied successfully",
            "preset_settings": {
                "subtitle_style": preset["subtitle_style"],
                "bgm_settings": preset["bgm_settings"],
                "video_settings": preset["video_settings"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply custom preset: {str(e)}"
        )


@router.get("/custom/by-project/{project_id}", response_model=CustomPresetResponse)
async def get_project_custom_preset(
    project_id: str,
    crud_manager: Neo4jCRUDManager = Depends(get_crud_manager)
):
    """
    프로젝트에 적용된 커스텀 프리셋 조회

    **Parameters:**
    - `project_id`: 프로젝트 ID

    **Returns:**
    - 적용된 프리셋 정보
    """
    try:
        preset = crud_manager.get_project_custom_preset(project_id)

        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No custom preset applied to project {project_id}"
            )

        return CustomPresetResponse(
            preset_id=preset["preset_id"],
            user_id="",  # 이 경우 user_id는 조회되지 않음
            name=preset["name"],
            description=preset.get("description"),
            subtitle_style=preset["subtitle_style"],
            bgm_settings=preset["bgm_settings"],
            video_settings=preset["video_settings"],
            is_favorite=preset["is_favorite"],
            usage_count=preset["usage_count"],
            created_at=preset["created_at"],
            updated_at=preset["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project custom preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project custom preset: {str(e)}"
        )

# ==================== Platform Preset Endpoints ====================

@router.get(
    "/platforms",
    response_model=List[PlatformPresetSummary],
    summary="플랫폼 프리셋 목록 조회"
)
async def get_platform_presets():
    """
    **모든 플랫폼 프리셋 목록 조회**

    지원하는 모든 플랫폼의 프리셋 요약 정보를 반환합니다.

    **지원 플랫폼:**
    - YouTube Shorts (youtube)
    - Instagram Reels (instagram)
    - TikTok (tiktok)
    - Facebook Reels (facebook)

    **반환값**: 플랫폼 프리셋 요약 리스트
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        presets = preset_service.get_all_platform_presets()

        logger.info(f"Retrieved {len(presets)} platform presets")
        return presets

    except Exception as e:
        logger.error(f"Failed to get platform presets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve platform presets: {str(e)}"
        )


@router.get(
    "/platforms/{platform}",
    response_model=PlatformPresetDetail,
    summary="특정 플랫폼 프리셋 상세 조회"
)
async def get_platform_preset(
    platform: Platform = Path(..., description="플랫폼 이름")
):
    """
    **특정 플랫폼 프리셋 상세 조회**

    플랫폼의 프리셋 전체 설정을 반환합니다.

    **경로 파라미터:**
    - **platform**: 플랫폼 이름 (youtube, instagram, tiktok, facebook)

    **반환값**: 플랫폼 프리셋 상세 정보
    - 해상도, 비트레이트, 프레임 레이트
    - 자막 스타일 설정
    - BGM 설정
    - 트랜지션 스타일
    - 색보정 프리셋
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        preset = preset_service.get_platform_preset(platform.value)

        logger.info(f"Retrieved preset detail for platform: {platform}")
        return preset

    except ValueError as e:
        logger.warning(f"Invalid platform requested: {platform}")
        raise HTTPException(
            status_code=404,
            detail=f"Platform preset not found: {platform}"
        )
    except Exception as e:
        logger.error(f"Failed to get preset for {platform}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve preset: {str(e)}"
        )


@router.post(
    "/projects/{project_id}/apply-platform-preset",
    response_model=PlatformPresetApplicationResponse,
    status_code=200,
    summary="프로젝트에 플랫폼 프리셋 적용"
)
async def apply_platform_preset_to_project(
    project_id: str = Path(..., description="프로젝트 ID"),
    request: PlatformPresetApplicationRequest = ...
):
    """
    **프로젝트에 플랫폼 프리셋 적용**

    선택한 플랫폼의 프리셋을 프로젝트에 적용합니다.
    적용된 프리셋은 Neo4j에 기록되며, 이후 영상 렌더링 시 사용됩니다.

    **경로 파라미터:**
    - **project_id**: 프로젝트 ID

    **요청 바디:**
    - **platform**: 적용할 플랫폼 프리셋 (youtube, instagram, tiktok, facebook)

    **반환값**: 적용된 프리셋 정보
    - 적용 시각
    - 적용 ID
    - 프리셋 전체 설정

    **처리 과정:**
    1. 프로젝트 존재 확인
    2. 플랫폼 프리셋 로드
    3. Neo4j에 적용 기록 생성
    4. 프로젝트-프리셋 관계 연결
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        result = preset_service.apply_preset_to_project(
            project_id=project_id,
            platform=request.platform.value
        )

        logger.info(
            f"Applied {request.platform} preset to project {project_id}"
        )

        return result

    except ValueError as e:
        logger.warning(f"Invalid input for apply preset: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to apply preset to project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply preset: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/current-platform-preset",
    response_model=PresetHistoryItem,
    summary="프로젝트의 현재 플랫폼 프리셋 조회"
)
async def get_project_current_platform_preset(
    project_id: str = Path(..., description="프로젝트 ID")
):
    """
    **프로젝트에 현재 적용된 플랫폼 프리셋 조회**

    프로젝트에 가장 최근에 적용된 플랫폼 프리셋을 반환합니다.

    **경로 파라미터:**
    - **project_id**: 프로젝트 ID

    **반환값**: 현재 적용된 프리셋 정보 (없으면 404)
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        preset = preset_service.get_project_current_preset(project_id)

        if not preset:
            raise HTTPException(
                status_code=404,
                detail=f"No platform preset applied to project: {project_id}"
            )

        logger.info(f"Retrieved current platform preset for project {project_id}")
        return preset

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current preset for project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve current preset: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/platform-preset-history",
    response_model=List[PresetHistoryItem],
    summary="프로젝트의 플랫폼 프리셋 적용 이력 조회"
)
async def get_project_platform_preset_history(
    project_id: str = Path(..., description="프로젝트 ID")
):
    """
    **프로젝트의 플랫폼 프리셋 적용 이력 조회**

    프로젝트에 적용된 모든 플랫폼 프리셋의 이력을 최신순으로 반환합니다.

    **경로 파라미터:**
    - **project_id**: 프로젝트 ID

    **반환값**: 프리셋 적용 이력 리스트 (최신순)
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        history = preset_service.get_project_preset_history(project_id)

        logger.info(
            f"Retrieved platform preset history for project {project_id}: "
            f"{len(history)} applications"
        )

        return history

    except Exception as e:
        logger.error(f"Failed to get preset history for project {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve preset history: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/validate-platform-preset/{platform}",
    response_model=PresetCompatibilityResponse,
    summary="프로젝트와 플랫폼 프리셋 호환성 검증"
)
async def validate_platform_preset_compatibility(
    project_id: str = Path(..., description="프로젝트 ID"),
    platform: Platform = Path(..., description="검증할 플랫폼")
):
    """
    **프로젝트와 플랫폼 프리셋 호환성 검증**

    프로젝트에 특정 플랫폼 프리셋을 적용하기 전에 호환성을 검증합니다.

    **검증 항목:**
    1. 프로젝트 플랫폼과 프리셋 플랫폼 일치 여부
    2. 스크립트 길이와 플랫폼 최대 길이 비교
    3. 기타 플랫폼별 제약사항

    **경로 파라미터:**
    - **project_id**: 프로젝트 ID
    - **platform**: 검증할 플랫폼

    **반환값**: 호환성 검증 결과
    - **compatible**: 호환 여부 (true/false)
    - **warnings**: 경고 메시지 리스트
    - **project_platform**: 프로젝트 플랫폼
    - **preset_platform**: 프리셋 플랫폼
    - **preset_max_duration**: 플랫폼 최대 영상 길이
    """
    try:
        neo4j_client = get_neo4j_client()
        preset_service = get_preset_service(neo4j_client)

        result = preset_service.validate_preset_compatibility(
            project_id=project_id,
            platform=platform.value
        )

        logger.info(
            f"Validated compatibility for project {project_id} with {platform}: "
            f"{'Compatible' if result['compatible'] else 'Has warnings'}"
        )

        return result

    except ValueError as e:
        logger.warning(f"Invalid input for validate compatibility: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to validate compatibility for project {project_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate compatibility: {str(e)}"
        )
