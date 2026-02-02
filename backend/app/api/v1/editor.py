"""비디오 편집 및 메타데이터 API

영상 메타데이터 조회 및 편집 관련 엔드포인트
클립 교체 및 대체 클립 관리
"""
from typing import List, Optional
import logging
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field

from app.services.video_metadata_service import get_video_metadata_service
from app.services.neo4j_client import get_neo4j_client
from app.services.clip_editor_service import get_clip_editor_service
from app.services.bgm_editor_service import get_bgm_editor_service
from app.services.subtitle_editor_service import get_subtitle_editor_service
from app.models.neo4j_models import (
    Neo4jCRUDManager,
    SectionAlternativeClipsResponse,
    GenerateAlternativeClipsRequest,
    ReplaceClipRequest,
    AlternativeClipResponse,
    CurrentClipResponse,
    BGMUpdateRequest,
    BGMInfoResponse,
    SubtitleStyleUpdateRequest,
    SubtitleStyleResponse,
    SubtitlePreviewRequest,
    SubtitlePreviewResponse
)
from app.core.config import get_settings

settings = get_settings()

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Response Models ====================

class VideoResolution(BaseModel):
    """비디오 해상도"""
    width: int = Field(..., description="가로 해상도 (픽셀)")
    height: int = Field(..., description="세로 해상도 (픽셀)")


class VideoSection(BaseModel):
    """비디오 섹션 정보"""
    type: str = Field(..., description="섹션 타입 (hook, body, cta)")
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    duration: float = Field(..., description="섹션 길이 (초)")


class VideoMetadataResponse(BaseModel):
    """비디오 메타데이터 응답"""
    project_id: str = Field(..., description="프로젝트 ID")
    video_id: str = Field(..., description="비디오 ID")
    video_path: str = Field(..., description="비디오 파일 경로")
    duration: float = Field(..., description="영상 길이 (초)")
    frame_rate: Optional[float] = Field(None, description="프레임 레이트 (FPS)")
    resolution: VideoResolution = Field(..., description="해상도")
    codec: Optional[str] = Field(None, description="비디오 코덱")
    audio_codec: Optional[str] = Field(None, description="오디오 코덱")
    bitrate: int = Field(..., description="비트레이트 (bps)")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    format_name: str = Field(..., description="포맷 이름")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    sections: List[VideoSection] = Field(default_factory=list, description="비디오 섹션 목록")


# ==================== Helper Functions ====================

def get_crud_manager() -> Neo4jCRUDManager:
    """Neo4j CRUD 매니저 인스턴스"""
    client = get_neo4j_client()
    return Neo4jCRUDManager(client)


# ==================== API Endpoints ====================

@router.get("/projects/{project_id}/video/metadata", response_model=VideoMetadataResponse)
async def get_project_video_metadata(project_id: str):
    """
    **프로젝트 영상 메타데이터 조회**

    프로젝트의 영상 파일에서 메타데이터를 추출합니다.
    FFmpeg의 ffprobe를 사용하여 영상 정보를 분석합니다.

    **추출 정보**:
    - 영상 길이, 해상도, 프레임 레이트
    - 비디오/오디오 코덱
    - 비트레이트, 파일 크기
    - 섹션 정보 (hook, body, cta)

    **요구사항**:
    - FFmpeg가 시스템에 설치되어 있어야 합니다.
    - 프로젝트에 연결된 비디오 파일이 존재해야 합니다.

    Args:
        project_id: 프로젝트 ID

    Returns:
        비디오 메타데이터

    Raises:
        404: 프로젝트 또는 비디오를 찾을 수 없음
        500: 메타데이터 추출 실패
    """
    try:
        crud = get_crud_manager()
        metadata_service = get_video_metadata_service()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. 프로젝트의 비디오 조회
        videos = crud.get_project_videos(project_id)
        if not videos:
            raise HTTPException(
                status_code=404,
                detail=f"No video found for project: {project_id}"
            )

        # 최신 비디오 선택
        video = videos[0]
        video_id = video["video_id"]
        video_path = video["file_path"]

        logger.info(f"Extracting metadata from video: {video_path}")

        # 3. FFmpeg로 메타데이터 추출
        metadata = metadata_service.extract_metadata(video_path)
        if not metadata:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract metadata from video: {video_path}. "
                       "Make sure FFmpeg is installed and the file exists."
            )

        # 4. Neo4j에서 섹션 정보 조회
        neo4j_client = get_neo4j_client()
        sections = metadata_service.get_video_sections(
            neo4j_client,
            project_id,
            video_id
        )

        # 5. 응답 생성
        return VideoMetadataResponse(
            project_id=project_id,
            video_id=video_id,
            video_path=metadata["video_path"],
            duration=metadata["duration"],
            frame_rate=metadata["frame_rate"],
            resolution=VideoResolution(
                width=metadata["resolution"]["width"],
                height=metadata["resolution"]["height"]
            ),
            codec=metadata["codec"],
            audio_codec=metadata["audio_codec"],
            bitrate=metadata["bitrate"],
            file_size=metadata["file_size"],
            format_name=metadata["format_name"],
            created_at=video.get("created_at"),
            sections=[VideoSection(**s) for s in sections]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/projects/{project_id}/videos/{video_id}/metadata", response_model=VideoMetadataResponse)
async def get_specific_video_metadata(project_id: str, video_id: str):
    """
    **특정 비디오 메타데이터 조회**

    프로젝트의 특정 비디오 파일에서 메타데이터를 추출합니다.

    Args:
        project_id: 프로젝트 ID
        video_id: 비디오 ID

    Returns:
        비디오 메타데이터

    Raises:
        404: 프로젝트 또는 비디오를 찾을 수 없음
        500: 메타데이터 추출 실패
    """
    try:
        crud = get_crud_manager()
        metadata_service = get_video_metadata_service()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. 특정 비디오 조회
        videos = crud.get_project_videos(project_id)
        video = next((v for v in videos if v["video_id"] == video_id), None)

        if not video:
            raise HTTPException(
                status_code=404,
                detail=f"Video {video_id} not found in project {project_id}"
            )

        video_path = video["file_path"]

        logger.info(f"Extracting metadata from video: {video_path}")

        # 3. FFmpeg로 메타데이터 추출
        metadata = metadata_service.extract_metadata(video_path)
        if not metadata:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract metadata from video: {video_path}. "
                       "Make sure FFmpeg is installed and the file exists."
            )

        # 4. Neo4j에서 섹션 정보 조회
        neo4j_client = get_neo4j_client()
        sections = metadata_service.get_video_sections(
            neo4j_client,
            project_id,
            video_id
        )

        # 5. 응답 생성
        return VideoMetadataResponse(
            project_id=project_id,
            video_id=video_id,
            video_path=metadata["video_path"],
            duration=metadata["duration"],
            frame_rate=metadata["frame_rate"],
            resolution=VideoResolution(
                width=metadata["resolution"]["width"],
                height=metadata["resolution"]["height"]
            ),
            codec=metadata["codec"],
            audio_codec=metadata["audio_codec"],
            bitrate=metadata["bitrate"],
            file_size=metadata["file_size"],
            format_name=metadata["format_name"],
            created_at=video.get("created_at"),
            sections=[VideoSection(**s) for s in sections]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# ==================== Clip Editor API Endpoints ====================

@router.get("/sections/{section_id}/alternative-clips", response_model=SectionAlternativeClipsResponse)
async def get_section_alternative_clips(section_id: str):
    """
    **섹션 대체 클립 목록 조회**

    섹션의 현재 클립과 대체 클립 3개를 조회합니다.

    Args:
        section_id: 섹션 ID

    Returns:
        현재 클립 및 대체 클립 목록

    Raises:
        404: 섹션을 찾을 수 없음
        500: 조회 실패
    """
    try:
        clip_editor = get_clip_editor_service()

        logger.info(f"Fetching alternative clips for section: {section_id}")

        # 클립 목록 조회
        result = await clip_editor.get_section_alternative_clips(section_id)

        # 응답 변환
        current_clip = None
        if result.get("current_clip"):
            clip_data = result["current_clip"]
            current_clip = CurrentClipResponse(
                clip_id=clip_data["clip_id"],
                video_path=clip_data["video_path"],
                thumbnail_url=clip_data["thumbnail_url"],
                prompt=clip_data["prompt"],
                created_at=str(clip_data.get("created_at", ""))
            )

        alternatives = [
            AlternativeClipResponse(
                clip_id=alt["clip_id"],
                video_path=alt["video_path"],
                thumbnail_url=alt["thumbnail_url"],
                prompt=alt["prompt"],
                variation=alt["variation"],
                created_at=str(alt.get("created_at", ""))
            )
            for alt in result.get("alternatives", [])
        ]

        return SectionAlternativeClipsResponse(
            section_id=section_id,
            current_clip=current_clip,
            alternatives=alternatives
        )

    except Exception as e:
        logger.error(f"Failed to get alternative clips: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alternative clips: {str(e)}"
        )


@router.post("/sections/{section_id}/alternative-clips")
async def generate_alternative_clips(
    section_id: str,
    request: GenerateAlternativeClipsRequest,
    background_tasks: BackgroundTasks
):
    """
    **대체 클립 생성 (AI)**

    섹션별로 AI가 3가지 변형의 대체 클립을 생성합니다.
    - 변형 1: 카메라 앵글 (close-up, medium shot, wide shot)
    - 변형 2: 조명 스타일 (natural, dramatic, soft)
    - 변형 3: 색감 (warm, cool, neutral)

    **생성 프로세스**:
    1. 원본 프롬프트에서 3가지 변형 생성
    2. Google Veo API로 영상 생성 (비동기)
    3. Cloudinary로 썸네일 생성
    4. Neo4j에 메타데이터 저장

    Args:
        section_id: 섹션 ID
        request: 생성 요청 (base_prompt, variations)
        background_tasks: FastAPI 백그라운드 작업

    Returns:
        생성 작업 정보

    Raises:
        404: 섹션을 찾을 수 없음
        500: 생성 실패
    """
    try:
        clip_editor = get_clip_editor_service()

        logger.info(
            f"Generating alternative clips for section {section_id}: "
            f"variations={request.variations}"
        )

        # 대체 클립 생성 시작 (비동기)
        clip_results = await clip_editor.generate_alternative_clips(
            section_id=section_id,
            base_prompt=request.base_prompt,
            variation_types=request.variations,
            duration=5,
            user_id=None,  # TODO: 인증 시스템에서 가져오기
            project_id=None
        )

        logger.info(f"Alternative clips generation initiated: {len(clip_results)} clips")

        return {
            "section_id": section_id,
            "status": "processing",
            "clips": clip_results,
            "message": f"{len(clip_results)} alternative clips are being generated. "
                      "Check status with GET /sections/{section_id}/alternative-clips"
        }

    except Exception as e:
        logger.error(f"Failed to generate alternative clips: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate alternative clips: {str(e)}"
        )


@router.patch("/sections/{section_id}/clip")
async def replace_section_clip(
    section_id: str,
    request: ReplaceClipRequest
):
    """
    **클립 교체 (원클릭)**

    섹션의 현재 클립을 대체 클립으로 교체합니다.

    **교체 로직**:
    1. 섹션의 기존 USES_CLIP 관계 삭제
    2. 새로운 클립과 USES_CLIP 관계 생성
    3. 기존 클립은 삭제하지 않고 보관 (롤백 가능)
    4. 최종 렌더링 시 새 클립 사용

    Args:
        section_id: 섹션 ID
        request: 교체 요청 (new_clip_id)

    Returns:
        교체 결과

    Raises:
        404: 섹션 또는 클립을 찾을 수 없음
        500: 교체 실패
    """
    try:
        clip_editor = get_clip_editor_service()

        logger.info(
            f"Replacing clip for section {section_id} with {request.new_clip_id}"
        )

        # 클립 교체
        success = await clip_editor.replace_section_clip(
            section_id=section_id,
            new_clip_id=request.new_clip_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to replace clip. Section or clip not found."
            )

        logger.info(f"Clip replaced successfully: {section_id} -> {request.new_clip_id}")

        return {
            "section_id": section_id,
            "new_clip_id": request.new_clip_id,
            "status": "success",
            "message": "Clip replaced successfully. Rendering will use the new clip."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to replace clip: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to replace clip: {str(e)}"
        )


@router.delete("/sections/{section_id}/alternative-clips/{clip_id}")
async def delete_alternative_clip(
    section_id: str,
    clip_id: str,
    delete_from_cloudinary: bool = True
):
    """
    **대체 클립 삭제**

    대체 클립을 삭제합니다. 선택적으로 Cloudinary에서도 삭제할 수 있습니다.

    Args:
        section_id: 섹션 ID
        clip_id: 클립 ID
        delete_from_cloudinary: Cloudinary에서도 삭제 여부 (기본: True)

    Returns:
        삭제 결과

    Raises:
        404: 클립을 찾을 수 없음
        500: 삭제 실패
    """
    try:
        clip_editor = get_clip_editor_service()

        logger.info(f"Deleting alternative clip: {clip_id}")

        # 클립 삭제
        success = await clip_editor.delete_alternative_clip(
            clip_id=clip_id,
            delete_from_cloudinary=delete_from_cloudinary
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Alternative clip not found: {clip_id}"
            )

        logger.info(f"Alternative clip deleted: {clip_id}")

        return {
            "section_id": section_id,
            "clip_id": clip_id,
            "status": "success",
            "message": "Alternative clip deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alternative clip: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alternative clip: {str(e)}"
        )


# ==================== Subtitle Style API ====================

@router.get("/projects/{project_id}/subtitles", response_model=SubtitleStyleResponse)
async def get_project_subtitle_style(project_id: str):
    """
    **프로젝트 자막 스타일 조회**

    프로젝트의 자막 스타일 설정을 조회합니다.
    설정이 없으면 기본 스타일을 반환합니다.

    **기본 스타일**:
    - 폰트: Arial 24px
    - 색상: 흰색 (#FFFFFF)
    - 배경: 반투명 검정 (#000000, 70%)
    - 위치: 하단 중앙
    - 아웃라인: 1px 검정

    Args:
        project_id: 프로젝트 ID

    Returns:
        자막 스타일 설정

    Raises:
        404: 프로젝트를 찾을 수 없음
        500: 서버 오류
    """
    try:
        crud = get_crud_manager()
        subtitle_service = get_subtitle_editor_service()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 자막 스타일 조회 (없으면 기본값)
        style = subtitle_service.get_project_style(project_id)

        # SRT 파일 경로 조회 (프로젝트의 비디오와 연결된 자막)
        srt_path = None
        videos = crud.get_project_videos(project_id)
        if videos:
            video = videos[0]
            video_path = Path(video["file_path"])
            potential_srt = video_path.with_suffix('.srt')
            if potential_srt.exists():
                srt_path = str(potential_srt)

        logger.info(f"Retrieved subtitle style for project {project_id}")

        return SubtitleStyleResponse(
            project_id=project_id,
            srt_file_path=srt_path,
            **style
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subtitle style: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/projects/{project_id}/subtitles", response_model=SubtitleStyleResponse)
async def update_project_subtitle_style(
    project_id: str,
    style_update: SubtitleStyleUpdateRequest
):
    """
    **프로젝트 자막 스타일 업데이트**

    자막의 폰트, 색상, 위치, 아웃라인, 그림자 등을 조정합니다.
    변경사항은 Neo4j에 저장되며, 이후 영상 생성 시 자동 적용됩니다.

    **조정 가능 항목**:
    - **폰트**: font_family (폰트 이름), font_size (24-72), font_color (HEX)
    - **배경**: background_color (HEX), background_opacity (0.0-1.0)
    - **위치**: position (top/center/bottom), vertical_offset (-100~100)
    - **정렬**: alignment (left/center/right)
    - **아웃라인**: outline_width (0-4), outline_color (HEX)
    - **그림자**: shadow_enabled (bool), shadow_offset_x/y (-10~10)

    Args:
        project_id: 프로젝트 ID
        style_update: 업데이트할 스타일 필드 (partial update)

    Returns:
        업데이트된 자막 스타일

    Raises:
        404: 프로젝트를 찾을 수 없음
        422: 유효하지 않은 스타일 값
        500: 서버 오류
    """
    try:
        crud = get_crud_manager()
        subtitle_service = get_subtitle_editor_service()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 스타일 업데이트
        updated_style = subtitle_service.update_project_style(
            project_id,
            style_update
        )

        logger.info(f"Updated subtitle style for project {project_id}")

        return updated_style

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subtitle style: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/projects/{project_id}/subtitles/preview", response_model=SubtitlePreviewResponse)
async def generate_subtitle_preview(
    project_id: str,
    preview_request: SubtitlePreviewRequest,
    background_tasks: BackgroundTasks
):
    """
    **자막 미리보기 생성**

    변경된 자막 스타일을 적용한 5초 샘플 영상을 생성합니다.
    미리보기 영상은 임시 파일로 저장되며, 1시간 후 자동 삭제됩니다.

    **워크플로우**:
    1. SRT 파일을 ASS 형식으로 변환 (스타일 적용)
    2. 원본 영상에서 지정 구간 추출
    3. ASS 자막 오버레이
    4. 임시 경로에 저장 및 URL 반환

    **사용 예시**:
    - 스타일 변경 후 바로 미리보기 확인
    - start_time을 조정하여 다른 구간 확인
    - 여러 스타일을 비교하여 최적 선택

    Args:
        project_id: 프로젝트 ID
        preview_request: 미리보기 요청 (시작 시간, 길이, 스타일)
        background_tasks: 백그라운드 작업 (만료된 파일 정리)

    Returns:
        미리보기 영상 URL 및 만료 시간

    Raises:
        404: 프로젝트 또는 비디오/자막 파일을 찾을 수 없음
        500: 미리보기 생성 실패 (FFmpeg 오류 등)
    """
    try:
        crud = get_crud_manager()
        subtitle_service = get_subtitle_editor_service()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 비디오 파일 조회
        videos = crud.get_project_videos(project_id)
        if not videos:
            raise HTTPException(
                status_code=404,
                detail=f"No video found for project: {project_id}"
            )

        video = videos[0]
        video_path = video["file_path"]

        # SRT 파일 조회
        srt_path = Path(video_path).with_suffix('.srt')
        if not srt_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"SRT file not found: {srt_path}. Generate subtitles first."
            )

        # 스타일 적용
        style = None
        if preview_request.style:
            # 임시 스타일 업데이트
            updated = subtitle_service.update_project_style(
                project_id,
                preview_request.style
            )
            style = {
                "font_family": updated.font_family,
                "font_size": updated.font_size,
                "font_color": updated.font_color,
                "background_color": updated.background_color,
                "background_opacity": updated.background_opacity,
                "position": updated.position,
                "vertical_offset": updated.vertical_offset,
                "alignment": updated.alignment,
                "outline_width": updated.outline_width,
                "outline_color": updated.outline_color,
                "shadow_enabled": updated.shadow_enabled,
                "shadow_offset_x": updated.shadow_offset_x,
                "shadow_offset_y": updated.shadow_offset_y
            }

        # 미리보기 생성
        result = subtitle_service.generate_preview(
            project_id=project_id,
            video_path=video_path,
            srt_path=str(srt_path),
            start_time=preview_request.start_time,
            duration=preview_request.duration,
            style=style
        )

        # 만료된 미리보기 파일 정리 (백그라운드)
        background_tasks.add_task(
            cleanup_expired_previews,
            result["expires_at"]
        )

        logger.info(f"Generated subtitle preview for project {project_id}")

        return SubtitlePreviewResponse(
            project_id=project_id,
            preview_url=f"/media/previews/{Path(result['preview_path']).name}",
            expires_at=result["expires_at"],
            style=SubtitleStyleResponse(
                project_id=project_id,
                **result["style"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate subtitle preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Helper Functions ====================

def cleanup_expired_previews(expires_at: datetime):
    """
    만료된 미리보기 파일 정리

    Args:
        expires_at: 만료 시간
    """
    import tempfile
    import time

    # 만료 시간까지 대기
    wait_seconds = (expires_at - datetime.now()).total_seconds()
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    # 임시 디렉토리의 만료된 파일 삭제
    temp_dir = Path(tempfile.gettempdir()) / "omnivibe_previews"
    if temp_dir.exists():
        for file in temp_dir.glob("preview_*.mp4"):
            try:
                if datetime.now() > expires_at:
                    file.unlink()
                    logger.debug(f"Deleted expired preview: {file}")
            except Exception as e:
                logger.warning(f"Failed to delete preview file {file}: {e}")
