"""Presentation API Pydantic Models"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class TransitionEffect(str, Enum):
    """영상 전환 효과"""
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    NONE = "none"


class PresentationStatus(str, Enum):
    """프리젠테이션 상태"""
    UPLOADED = "uploaded"  # PDF 업로드 완료
    SCRIPT_GENERATED = "script_generated"  # 스크립트 생성 완료
    AUDIO_GENERATED = "audio_generated"  # 오디오 생성 완료
    TIMING_ANALYZED = "timing_analyzed"  # 타이밍 분석 완료
    VIDEO_RENDERING = "video_rendering"  # 영상 렌더링 중
    VIDEO_READY = "video_ready"  # 영상 생성 완료
    FAILED = "failed"  # 실패


# ==================== Request Models ====================

class PresentationUploadRequest(BaseModel):
    """PDF 업로드 요청"""
    project_id: str = Field(..., description="프로젝트 ID")
    dpi: int = Field(200, description="슬라이드 이미지 해상도 (DPI)")
    lang: str = Field("kor+eng", description="OCR 언어 (pytesseract 형식)")


class GenerateScriptRequest(BaseModel):
    """나레이션 스크립트 생성 요청"""
    tone: str = Field("professional", description="어조 (professional/friendly/educational)")
    target_duration_per_slide: float = Field(
        15.0,
        description="슬라이드당 목표 시간 (초)",
        ge=5.0,
        le=60.0
    )
    include_slide_numbers: bool = Field(
        False,
        description="슬라이드 번호 포함 여부"
    )


class GenerateAudioRequest(BaseModel):
    """TTS 오디오 생성 요청"""
    voice_id: Optional[str] = Field(None, description="음성 ID (없으면 기본값 사용)")
    script: Optional[str] = Field(None, description="스크립트 (없으면 기존 스크립트 사용)")
    model: str = Field("tts-1", description="TTS 모델 (tts-1 또는 tts-1-hd)")


class AnalyzeTimingRequest(BaseModel):
    """타이밍 분석 요청"""
    audio_path: Optional[str] = Field(None, description="오디오 파일 경로 (없으면 기존 오디오 사용)")
    manual_timings: Optional[List[float]] = Field(
        None,
        description="수동 타이밍 (초 단위, 슬라이드 수만큼)"
    )


class GenerateVideoRequest(BaseModel):
    """프리젠테이션 영상 생성 요청"""
    transition_effect: TransitionEffect = Field(
        TransitionEffect.FADE,
        description="전환 효과"
    )
    transition_duration: float = Field(
        0.5,
        description="전환 시간 (초)",
        ge=0.0,
        le=2.0
    )
    bgm_path: Optional[str] = Field(None, description="배경음악 파일 경로")
    bgm_volume: float = Field(0.3, description="배경음악 볼륨 (0.0~1.0)", ge=0.0, le=1.0)


# ==================== Response Models ====================

class SlideInfo(BaseModel):
    """슬라이드 정보"""
    slide_number: int = Field(..., description="슬라이드 번호 (1부터 시작)")
    image_path: str = Field(..., description="슬라이드 이미지 파일 경로")
    ocr_text: Optional[str] = Field(None, description="OCR 추출 텍스트")
    script: Optional[str] = Field(None, description="나레이션 스크립트")
    start_time: Optional[float] = Field(None, description="시작 시간 (초)")
    end_time: Optional[float] = Field(None, description="종료 시간 (초)")
    duration: Optional[float] = Field(None, description="표시 시간 (초)")


class PresentationUploadResponse(BaseModel):
    """PDF 업로드 응답"""
    presentation_id: str = Field(..., description="프리젠테이션 ID")
    pdf_path: str = Field(..., description="저장된 PDF 파일 경로")
    total_slides: int = Field(..., description="총 슬라이드 수")
    slides: List[SlideInfo] = Field(..., description="슬라이드 목록")
    status: PresentationStatus = Field(..., description="프리젠테이션 상태")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerateScriptResponse(BaseModel):
    """스크립트 생성 응답"""
    presentation_id: str
    full_script: str = Field(..., description="전체 나레이션 스크립트")
    slides: List[SlideInfo] = Field(..., description="슬라이드별 스크립트")
    estimated_total_duration: float = Field(..., description="예상 총 시간 (초)")
    status: PresentationStatus


class GenerateAudioResponse(BaseModel):
    """오디오 생성 응답"""
    presentation_id: str
    audio_path: str = Field(..., description="생성된 오디오 파일 경로")
    duration: float = Field(..., description="오디오 길이 (초)")
    whisper_result: Dict[str, Any] = Field(..., description="Whisper STT 검증 결과")
    accuracy: float = Field(..., description="텍스트 정확도 (0.0~1.0)")
    status: PresentationStatus


class AnalyzeTimingResponse(BaseModel):
    """타이밍 분석 응답"""
    presentation_id: str
    slides: List[SlideInfo] = Field(..., description="슬라이드별 타이밍 정보")
    total_duration: float = Field(..., description="총 영상 길이 (초)")
    status: PresentationStatus


class GenerateVideoResponse(BaseModel):
    """영상 생성 응답"""
    presentation_id: str
    video_path: Optional[str] = Field(None, description="생성된 영상 파일 경로")
    celery_task_id: str = Field(..., description="Celery 작업 ID (비동기)")
    status: PresentationStatus
    estimated_completion_time: Optional[int] = Field(
        None,
        description="예상 완료 시간 (초)"
    )


class PresentationDetailResponse(BaseModel):
    """프리젠테이션 상세 정보"""
    presentation_id: str
    project_id: str
    pdf_path: str
    total_slides: int
    slides: List[SlideInfo]
    full_script: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    status: PresentationStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class PresentationListItem(BaseModel):
    """프리젠테이션 목록 아이템"""
    presentation_id: str
    project_id: str
    total_slides: int
    status: PresentationStatus
    created_at: datetime
    updated_at: datetime
    thumbnail_url: Optional[str] = None  # 첫 슬라이드 썸네일


class PresentationListResponse(BaseModel):
    """프리젠테이션 목록 응답"""
    presentations: List[PresentationListItem]
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")


# ==================== Internal Models (Neo4j) ====================

class PresentationModel(BaseModel):
    """프리젠테이션 Neo4j 모델"""
    presentation_id: str = Field(
        default_factory=lambda: f"pres_{uuid.uuid4().hex[:12]}"
    )
    project_id: str
    pdf_path: str
    total_slides: int
    slides_data: List[Dict[str, Any]] = Field(default_factory=list)
    full_script: Optional[str] = None
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None
    video_path: Optional[str] = None
    status: PresentationStatus = PresentationStatus.UPLOADED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
