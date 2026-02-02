"""BGM (배경음악) 편집 API

영상 배경음악의 볼륨, 페이드, 구간을 조정하는 API
"""
from typing import Optional
import logging
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.services.neo4j_client import get_neo4j_client
from app.services.bgm_editor_service import get_bgm_editor_service
from app.models.neo4j_models import (
    Neo4jCRUDManager,
    BGMUpdateRequest,
    BGMInfoResponse
)
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

def get_crud_manager() -> Neo4jCRUDManager:
    """Neo4j CRUD 매니저 인스턴스"""
    client = get_neo4j_client()
    return Neo4jCRUDManager(client)


# ==================== BGM API Endpoints ====================

@router.get("/projects/{project_id}/bgm", response_model=BGMInfoResponse)
async def get_project_bgm_settings(project_id: str):
    """
    **프로젝트 BGM 설정 조회**

    프로젝트의 배경음악(BGM) 설정을 조회합니다.

    **반환 정보**:
    - BGM 파일 경로
    - 볼륨, 페이드 인/아웃 설정
    - 루프 및 덕킹 설정

    Args:
        project_id: 프로젝트 ID

    Returns:
        BGM 설정 정보

    Raises:
        404: 프로젝트 또는 BGM 설정을 찾을 수 없음
    """
    try:
        crud = get_crud_manager()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. BGM 설정 조회
        bgm_settings = crud.get_bgm_settings(project_id)
        if not bgm_settings:
            raise HTTPException(
                status_code=404,
                detail=f"BGM settings not found for project: {project_id}"
            )

        # 3. 응답 생성
        return BGMInfoResponse(
            project_id=project_id,
            **bgm_settings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get BGM settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/projects/{project_id}/bgm")
async def update_project_bgm_settings(
    project_id: str,
    bgm_update: BGMUpdateRequest
):
    """
    **프로젝트 BGM 설정 업데이트**

    프로젝트의 BGM 설정을 부분적으로 업데이트합니다.

    **업데이트 가능 필드**:
    - volume: 볼륨 (0.0-1.0)
    - fade_in_duration: 페이드 인 길이 (초)
    - fade_out_duration: 페이드 아웃 길이 (초)
    - start_time: BGM 시작 시간 (초)
    - end_time: BGM 종료 시간 (null이면 끝까지)
    - loop: 반복 재생 여부
    - ducking_enabled: 덕킹 활성화 여부
    - ducking_level: 덕킹 볼륨 레벨 (0.1-0.5)

    Args:
        project_id: 프로젝트 ID
        bgm_update: 업데이트할 설정

    Returns:
        업데이트된 BGM 설정

    Raises:
        404: 프로젝트 또는 BGM 설정을 찾을 수 없음
    """
    try:
        crud = get_crud_manager()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. BGM 설정 존재 확인
        existing_bgm = crud.get_bgm_settings(project_id)
        if not existing_bgm:
            raise HTTPException(
                status_code=404,
                detail=f"BGM settings not found for project: {project_id}. "
                       "Please upload a BGM file first."
            )

        # 3. None이 아닌 필드만 업데이트
        updates = {
            k: v for k, v in bgm_update.model_dump().items()
            if v is not None
        }

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )

        # 4. BGM 설정 업데이트
        success = crud.update_bgm_settings(project_id, updates)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update BGM settings"
            )

        # 5. 업데이트된 설정 조회
        updated_settings = crud.get_bgm_settings(project_id)

        return BGMInfoResponse(
            project_id=project_id,
            **updated_settings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update BGM settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/projects/{project_id}/bgm/upload")
async def upload_project_bgm(
    project_id: str,
    bgm_file: UploadFile = File(...),
    volume: float = 0.3,
    fade_in_duration: float = 2.0,
    fade_out_duration: float = 2.0,
    start_time: float = 0.0,
    loop: bool = True,
    ducking_enabled: bool = True,
    ducking_level: float = 0.3
):
    """
    **프로젝트 BGM 파일 업로드**

    프로젝트에 배경음악 파일을 업로드하고 초기 설정을 저장합니다.

    **지원 포맷**: MP3, WAV, AAC, FLAC, OGG, M4A

    Args:
        project_id: 프로젝트 ID
        bgm_file: BGM 파일 (multipart/form-data)
        volume: 볼륨 (0.0-1.0)
        fade_in_duration: 페이드 인 길이 (초)
        fade_out_duration: 페이드 아웃 길이 (초)
        start_time: BGM 시작 시간 (초)
        loop: 반복 재생 여부
        ducking_enabled: 덕킹 활성화 여부
        ducking_level: 덕킹 볼륨 레벨 (0.1-0.5)

    Returns:
        BGM 설정 정보

    Raises:
        404: 프로젝트를 찾을 수 없음
        400: 지원하지 않는 파일 형식
    """
    try:
        crud = get_crud_manager()
        bgm_service = get_bgm_editor_service()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. 파일 확장자 확인
        file_extension = Path(bgm_file.filename).suffix.lower()
        supported_formats = [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"]

        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_extension}. "
                       f"Supported formats: {', '.join(supported_formats)}"
            )

        # 3. BGM 파일 저장
        bgm_dir = Path(settings.AUDIO_OUTPUT_DIR) / "bgm"
        bgm_dir.mkdir(parents=True, exist_ok=True)

        bgm_file_path = bgm_dir / f"{project_id}_bgm{file_extension}"

        with open(bgm_file_path, "wb") as f:
            content = await bgm_file.read()
            f.write(content)

        logger.info(f"BGM file uploaded: {bgm_file_path}")

        # 4. 파일 검증
        if not bgm_service.validate_audio_file(str(bgm_file_path)):
            # 검증 실패 시 파일 삭제
            os.remove(bgm_file_path)
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file. Please check the file format and content."
            )

        # 5. BGM 설정 저장
        bgm_settings = {
            "bgm_file_path": str(bgm_file_path),
            "volume": volume,
            "fade_in_duration": fade_in_duration,
            "fade_out_duration": fade_out_duration,
            "start_time": start_time,
            "end_time": None,
            "loop": loop,
            "ducking_enabled": ducking_enabled,
            "ducking_level": ducking_level,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        saved_settings = crud.create_or_update_bgm_settings(project_id, bgm_settings)

        if not saved_settings:
            # 저장 실패 시 파일 삭제
            os.remove(bgm_file_path)
            raise HTTPException(
                status_code=500,
                detail="Failed to save BGM settings"
            )

        return BGMInfoResponse(
            project_id=project_id,
            **saved_settings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload BGM: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/projects/{project_id}/bgm")
async def delete_project_bgm(project_id: str):
    """
    **프로젝트 BGM 삭제**

    프로젝트의 BGM 설정 및 업로드된 파일을 삭제합니다.

    Args:
        project_id: 프로젝트 ID

    Returns:
        삭제 성공 메시지

    Raises:
        404: 프로젝트 또는 BGM 설정을 찾을 수 없음
    """
    try:
        crud = get_crud_manager()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. BGM 설정 조회
        bgm_settings = crud.get_bgm_settings(project_id)
        if not bgm_settings:
            raise HTTPException(
                status_code=404,
                detail=f"BGM settings not found for project: {project_id}"
            )

        # 3. BGM 파일 삭제 (파일이 존재하면)
        bgm_file_path = bgm_settings.get("bgm_file_path")
        if bgm_file_path and os.path.exists(bgm_file_path):
            try:
                os.remove(bgm_file_path)
                logger.info(f"Deleted BGM file: {bgm_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete BGM file: {e}")

        # 4. Neo4j에서 BGM 설정 삭제
        success = crud.delete_bgm_settings(project_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete BGM settings"
            )

        return {
            "message": "BGM deleted successfully",
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete BGM: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
