"""Brand Template Pydantic Models"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# ==================== Sub-Models ====================

class IntroConfig(BaseModel):
    """인트로 설정"""
    enabled: bool = Field(True, description="인트로 활성화 여부")
    duration: float = Field(3.0, description="인트로 길이 (초)", ge=0.5, le=30.0)
    script: str = Field(
        "",
        description="인트로 나레이션 스크립트 ({{변수}} 지원)"
    )
    background_image: Optional[str] = Field(None, description="배경 이미지 경로 (로고 등)")
    background_color: str = Field("#16325C", description="배경 색상 (hex)")
    title_template: str = Field("{{presentation_title}}", description="제목 템플릿")
    subtitle_template: str = Field("{{date}} | {{author}}", description="부제목 템플릿")


class OutroConfig(BaseModel):
    """아웃트로 설정"""
    enabled: bool = Field(True, description="아웃트로 활성화 여부")
    duration: float = Field(4.0, description="아웃트로 길이 (초)", ge=0.5, le=30.0)
    script: str = Field(
        "",
        description="아웃트로 나레이션 스크립트 ({{변수}} 지원)"
    )
    background_image: Optional[str] = Field(None, description="배경 이미지 경로")
    contact_info: str = Field("", description="연락처 정보")
    cta_text: str = Field("구독 · 좋아요 · 공유", description="CTA 텍스트")


class VoiceConfig(BaseModel):
    """음성 설정"""
    voice_id: str = Field("onyx", description="음성 ID (ElevenLabs 또는 OpenAI)")
    speed: float = Field(1.0, description="음성 속도 (0.5~2.0)", ge=0.5, le=2.0)
    engine: str = Field("openai", description="TTS 엔진 (openai / elevenlabs)")


# ==================== Request Models ====================

class BrandTemplateCreateRequest(BaseModel):
    """브랜드 템플릿 생성 요청"""
    project_id: str = Field(..., description="프로젝트 ID")
    name: str = Field(..., description="템플릿 이름", min_length=1, max_length=100)
    is_default: bool = Field(False, description="기본 템플릿 여부")
    intro: IntroConfig = Field(default_factory=IntroConfig, description="인트로 설정")
    outro: OutroConfig = Field(default_factory=OutroConfig, description="아웃트로 설정")
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig, description="음성 설정")


class BrandTemplateUpdateRequest(BaseModel):
    """브랜드 템플릿 수정 요청"""
    name: Optional[str] = Field(None, description="템플릿 이름", min_length=1, max_length=100)
    is_default: Optional[bool] = Field(None, description="기본 템플릿 여부")
    intro: Optional[IntroConfig] = Field(None, description="인트로 설정")
    outro: Optional[OutroConfig] = Field(None, description="아웃트로 설정")
    voice_config: Optional[VoiceConfig] = Field(None, description="음성 설정")


# ==================== Core Model ====================

class BrandTemplate(BaseModel):
    """브랜드 템플릿"""
    id: str = Field(
        default_factory=lambda: f"bt_{uuid.uuid4().hex[:12]}",
        description="템플릿 ID"
    )
    project_id: str = Field(..., description="프로젝트 ID")
    name: str = Field(..., description="템플릿 이름")
    is_default: bool = Field(False, description="기본 템플릿 여부")
    intro: IntroConfig = Field(default_factory=IntroConfig, description="인트로 설정")
    outro: OutroConfig = Field(default_factory=OutroConfig, description="아웃트로 설정")
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig, description="음성 설정")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성일시")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정일시")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Response Models ====================

class BrandTemplateResponse(BaseModel):
    """브랜드 템플릿 응답"""
    id: str
    project_id: str
    name: str
    is_default: bool
    intro: IntroConfig
    outro: OutroConfig
    voice_config: VoiceConfig
    created_at: datetime
    updated_at: datetime


class BrandTemplateListResponse(BaseModel):
    """브랜드 템플릿 목록 응답"""
    templates: list[BrandTemplateResponse] = Field(..., description="템플릿 목록")
    total: int = Field(..., description="전체 개수")
    project_id: str = Field(..., description="프로젝트 ID")


class BrandTemplateDeleteResponse(BaseModel):
    """브랜드 템플릿 삭제 응답"""
    id: str = Field(..., description="삭제된 템플릿 ID")
    message: str = Field(..., description="결과 메시지")
