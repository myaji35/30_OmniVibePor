"""Video Rendering API 엔드포인트"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

from app.services.video_renderer import get_video_renderer, PLATFORM_SPECS, TRANSITION_EFFECTS, SUBTITLE_STYLES

router = APIRouter()
logger = logging.getLogger(__name__)


class VideoRenderRequest(BaseModel):
    """영상 렌더링 요청"""
    video_clips: List[str] = Field(..., min_items=1, description="영상 클립 경로 리스트")
    audio_path: str = Field(..., description="나레이션 오디오 경로")
    output_filename: Optional[str] = Field(None, description="출력 파일명 (자동 생성 시 생략)")
    subtitle_path: Optional[str] = Field(None, description="자막 파일 경로 (.srt)")
    transitions: Optional[List[str]] = Field(None, description="전환 효과 리스트 (클립 개수 - 1)")
    bgm_path: Optional[str] = Field(None, description="배경음악 경로")
    bgm_volume: float = Field(0.2, ge=0.0, le=1.0, description="BGM 볼륨 (0.0-1.0)")
    transition_duration: float = Field(0.5, ge=0.1, le=2.0, description="전환 효과 지속 시간 (초)")
    platform: Optional[str] = Field(None, description="플랫폼별 최적화 (youtube, instagram, tiktok 등)")


class VideoRenderResponse(BaseModel):
    """영상 렌더링 응답"""
    status: str
    output_path: str
    file_size_mb: float
    render_time: float
    steps: dict


@router.post("/render", response_model=VideoRenderResponse)
async def render_video(request: VideoRenderRequest):
    """
    영상 렌더링 (전체 파이프라인)

    **워크플로우**:
    1. 클립 병합 (전환 효과 적용)
    2. 오디오 믹싱 (나레이션 + BGM)
    3. 자막 오버레이
    4. 플랫폼별 최적화

    **예시 요청**:
    ```json
    {
        "video_clips": [
            "./outputs/videos/clip1.mp4",
            "./outputs/videos/clip2.mp4",
            "./outputs/videos/clip3.mp4"
        ],
        "audio_path": "./outputs/audio/narration.mp3",
        "subtitle_path": "./outputs/subtitles/script.srt",
        "transitions": ["fade", "wipeleft", "slideup"],
        "bgm_path": "./assets/bgm/background.mp3",
        "bgm_volume": 0.2,
        "platform": "youtube"
    }
    ```

    **응답**:
    ```json
    {
        "status": "success",
        "output_path": "./outputs/videos/final_1234567890.mp4",
        "file_size_mb": 45.67,
        "render_time": 12.34,
        "steps": {
            "merge_clips": {...},
            "audio_mix": {...},
            "subtitles": {...},
            "platform_optimize": {...}
        }
    }
    ```
    """
    try:
        logger.info(f"Starting video render request: {len(request.video_clips)} clips")

        # 파일 존재 확인
        for clip in request.video_clips:
            if not Path(clip).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Video clip not found: {clip}"
                )

        if not Path(request.audio_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {request.audio_path}"
            )

        if request.subtitle_path and not Path(request.subtitle_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Subtitle file not found: {request.subtitle_path}"
            )

        if request.bgm_path and not Path(request.bgm_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"BGM file not found: {request.bgm_path}"
            )

        # 플랫폼 검증
        if request.platform and request.platform not in PLATFORM_SPECS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown platform '{request.platform}'. "
                       f"Available: {', '.join(PLATFORM_SPECS.keys())}"
            )

        # 전환 효과 개수 검증
        if request.transitions:
            expected = len(request.video_clips) - 1
            if len(request.transitions) != expected:
                raise HTTPException(
                    status_code=400,
                    detail=f"Transition count mismatch: expected {expected}, got {len(request.transitions)}"
                )

            # 전환 효과 유효성 검증
            invalid_transitions = [t for t in request.transitions if t not in TRANSITION_EFFECTS]
            if invalid_transitions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transitions: {invalid_transitions}. "
                           f"See /video/transitions for available options."
                )

        # 출력 경로 생성
        renderer = get_video_renderer()
        import time

        if request.output_filename:
            output_path = str(renderer.output_dir / request.output_filename)
        else:
            output_path = str(renderer.output_dir / f"final_{int(time.time())}.mp4")

        # 렌더링 실행
        result = await renderer.render_video(
            video_clips=request.video_clips,
            audio_path=request.audio_path,
            output_path=output_path,
            subtitle_path=request.subtitle_path,
            transitions=request.transitions,
            bgm_path=request.bgm_path,
            bgm_volume=request.bgm_volume,
            transition_duration=request.transition_duration,
            platform=request.platform
        )

        return VideoRenderResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video render failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transitions")
async def list_transitions():
    """
    사용 가능한 전환 효과 목록

    **응답 예시**:
    ```json
    {
        "transitions": {
            "fade": "페이드 전환 (기본)",
            "wipeleft": "왼쪽에서 와이프",
            "slideleft": "왼쪽으로 슬라이드",
            ...
        },
        "total": 31
    }
    ```
    """
    renderer = get_video_renderer()
    transitions = renderer.get_available_transitions()

    return {
        "transitions": transitions,
        "total": len(transitions)
    }


@router.get("/platforms")
async def list_platforms():
    """
    사용 가능한 플랫폼 목록

    **응답 예시**:
    ```json
    {
        "platforms": {
            "youtube": {
                "description": "YouTube 최적화 (Full HD, 16:9)",
                "resolution": "1920x1080",
                "bitrate": "8M",
                "fps": 30
            },
            "instagram": {
                "description": "Instagram 피드 최적화 (4:5)",
                "resolution": "1080x1350",
                "bitrate": "5M",
                "fps": 30
            },
            ...
        }
    }
    ```
    """
    platforms = {}
    for name, spec in PLATFORM_SPECS.items():
        platforms[name] = {
            "description": spec["description"],
            "resolution": spec["resolution"],
            "bitrate": spec["bitrate"],
            "fps": spec["fps"]
        }

    return {"platforms": platforms}


@router.get("/subtitle-styles")
async def list_subtitle_styles():
    """
    사용 가능한 자막 스타일 목록

    **응답 예시**:
    ```json
    {
        "styles": {
            "default": "기본 스타일 (하단 중앙, 흰색 글자, 검은색 테두리)",
            "youtube": "YouTube 스타일 (큰 폰트, 하단 중앙)",
            "tiktok": "TikTok 스타일 (노란색, 중앙, 큰 폰트)",
            ...
        }
    }
    ```
    """
    renderer = get_video_renderer()
    styles = renderer.get_available_subtitle_styles()

    return {"styles": styles}


class MergeClipsRequest(BaseModel):
    """클립 병합 요청"""
    clips: List[str] = Field(..., min_items=2, description="영상 클립 경로 리스트")
    output_filename: Optional[str] = Field(None, description="출력 파일명")
    transitions: Optional[List[str]] = Field(None, description="전환 효과 리스트")
    transition_duration: float = Field(0.5, ge=0.1, le=2.0, description="전환 효과 지속 시간 (초)")


@router.post("/merge-clips")
async def merge_clips(request: MergeClipsRequest):
    """
    클립 병합 (전환 효과 지원)

    **사용 사례**:
    - 여러 장면을 하나의 영상으로 병합
    - 전환 효과 적용

    **예시**:
    ```json
    {
        "clips": [
            "./outputs/videos/scene1.mp4",
            "./outputs/videos/scene2.mp4",
            "./outputs/videos/scene3.mp4"
        ],
        "transitions": ["fade", "wipeleft"],
        "transition_duration": 0.5
    }
    ```
    """
    try:
        # 파일 존재 확인
        for clip in request.clips:
            if not Path(clip).exists():
                raise HTTPException(status_code=404, detail=f"Clip not found: {clip}")

        # 전환 효과 검증
        if request.transitions:
            expected = len(request.clips) - 1
            if len(request.transitions) != expected:
                raise HTTPException(
                    status_code=400,
                    detail=f"Transition count mismatch: expected {expected}, got {len(request.transitions)}"
                )

        # 출력 경로
        renderer = get_video_renderer()
        import time

        if request.output_filename:
            output_path = str(renderer.output_dir / request.output_filename)
        else:
            output_path = str(renderer.output_dir / f"merged_{int(time.time())}.mp4")

        # 병합 실행
        result = renderer.merge_clips(
            clips=request.clips,
            output_path=output_path,
            transitions=request.transitions,
            transition_duration=request.transition_duration
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Merge clips failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class OptimizeRequest(BaseModel):
    """플랫폼 최적화 요청"""
    video_path: str = Field(..., description="입력 영상 경로")
    platform: str = Field(..., description="플랫폼 (youtube, instagram, tiktok 등)")
    output_filename: Optional[str] = Field(None, description="출력 파일명")


@router.post("/optimize")
async def optimize_video(request: OptimizeRequest):
    """
    플랫폼별 최적화

    **사용 사례**:
    - YouTube 용 Full HD 16:9 변환
    - Instagram 피드용 4:5 변환
    - TikTok/Instagram 스토리용 9:16 변환

    **예시**:
    ```json
    {
        "video_path": "./outputs/videos/original.mp4",
        "platform": "instagram",
        "output_filename": "instagram_optimized.mp4"
    }
    ```
    """
    try:
        # 파일 존재 확인
        if not Path(request.video_path).exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {request.video_path}")

        # 플랫폼 검증
        if request.platform not in PLATFORM_SPECS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown platform '{request.platform}'. "
                       f"Available: {', '.join(PLATFORM_SPECS.keys())}"
            )

        # 출력 경로
        renderer = get_video_renderer()
        import time

        if request.output_filename:
            output_path = str(renderer.output_dir / request.output_filename)
        else:
            output_path = str(renderer.output_dir / f"{request.platform}_{int(time.time())}.mp4")

        # 최적화 실행
        result = renderer.optimize_for_platform(
            video_path=request.video_path,
            platform=request.platform,
            output_path=output_path
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_video(filename: str):
    """
    렌더링된 영상 다운로드

    **사용법**:
    1. /video/render로 렌더링
    2. 응답의 output_path에서 파일명 추출
    3. /video/download/{filename}으로 다운로드
    """
    try:
        renderer = get_video_renderer()
        video_path = renderer.output_dir / filename

        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {filename}")

        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    VideoRenderer 헬스 체크

    **확인 항목**:
    - FFmpeg 설치 여부
    - 출력 디렉토리 쓰기 권한
    """
    try:
        renderer = get_video_renderer()

        # FFmpeg 버전 확인
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        ffmpeg_version = result.stdout.decode().split('\n')[0]

        # 출력 디렉토리 확인
        output_dir_writable = renderer.output_dir.exists() and renderer.output_dir.is_dir()

        return {
            "status": "healthy",
            "ffmpeg_version": ffmpeg_version,
            "output_dir": str(renderer.output_dir),
            "output_dir_writable": output_dir_writable
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
