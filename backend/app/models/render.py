"""렌더링 관련 Pydantic 모델

멀티포맷 영상 렌더링을 위한 요청/응답 모델:
- VideoFormat: YouTube, Instagram, TikTok 포맷
- RenderQuality: 품질 설정
- ScriptBlockData: 스크립트 블록 (hook, intro, body, cta, outro)
- RenderRequest/Status/Result: 렌더링 요청 및 상태 관리
"""
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class VideoFormat(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class RenderQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScriptBlockData(BaseModel):
    id: Optional[int] = None
    type: str  # hook, intro, body, cta, outro
    text: str
    startTime: float
    duration: float
    backgroundUrl: Optional[str] = None
    animation: Optional[str] = None
    fontSize: Optional[int] = None
    textColor: Optional[str] = None
    textAlign: Optional[str] = None


class BrandingData(BaseModel):
    logo: str = ""
    primaryColor: str = "#00A1E0"
    secondaryColor: Optional[str] = None
    fontFamily: Optional[str] = None


class RenderRequest(BaseModel):
    composition_id: str  # youtube, instagram, tiktok
    blocks: List[ScriptBlockData]
    audio_url: str = ""
    branding: BrandingData = BrandingData()
    quality: RenderQuality = RenderQuality.MEDIUM
    formats: List[VideoFormat] = [VideoFormat.YOUTUBE]


class RenderStatus(BaseModel):
    task_id: str
    status: str  # pending, in_progress, completed, failed
    progress: int = 0
    format: Optional[str] = None
    output_url: Optional[str] = None
    error: Optional[str] = None


class RenderResult(BaseModel):
    task_id: str
    results: dict  # format -> url mapping
    total_duration: float
