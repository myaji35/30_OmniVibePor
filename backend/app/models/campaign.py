"""캠페인 모델 (프론트엔드 Studio와 연동)

캠페인(Campaign)은 콘텐츠 제작의 최상위 개념으로,
클라이언트별로 일관된 컨셉과 리소스를 관리합니다.

구조:
- Client (1) -> Campaign (N)
- Campaign (1) -> ContentSchedule (N)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CampaignStatus(str, Enum):
    """캠페인 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ConceptGender(str, Enum):
    """컨셉 성별"""
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


class ConceptTone(str, Enum):
    """컨셉 톤"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    HUMOROUS = "humorous"
    SERIOUS = "serious"


class ConceptStyle(str, Enum):
    """컨셉 스타일"""
    SOFT = "soft"
    INTENSE = "intense"
    CALM = "calm"
    ENERGETIC = "energetic"


class CampaignBase(BaseModel):
    """캠페인 기본 모델"""
    client_id: int = Field(..., description="클라이언트 ID")
    name: str = Field(..., min_length=1, max_length=200, description="캠페인 이름")

    # 컨셉 정보
    concept_gender: Optional[ConceptGender] = Field(None, description="컨셉 성별")
    concept_tone: Optional[ConceptTone] = Field(None, description="컨셉 톤")
    concept_style: Optional[ConceptStyle] = Field(None, description="컨셉 스타일")

    # 콘텐츠 설정
    target_duration: Optional[int] = Field(None, ge=10, le=600, description="목표 영상 길이 (초)")

    # 음성 설정
    voice_id: Optional[str] = Field(None, description="ElevenLabs Voice ID")
    voice_name: Optional[str] = Field(None, description="음성 이름 (표시용)")

    # 인트로/엔딩 설정
    intro_video_url: Optional[str] = Field(None, description="인트로 영상 URL (Cloudinary)")
    intro_duration: int = Field(5, ge=0, le=10, description="인트로 길이 (초)")
    outro_video_url: Optional[str] = Field(None, description="엔딩 영상 URL (Cloudinary)")
    outro_duration: int = Field(5, ge=0, le=10, description="엔딩 길이 (초)")

    # BGM 설정
    bgm_url: Optional[str] = Field(None, description="배경음악 URL (Cloudinary)")
    bgm_volume: float = Field(0.3, ge=0.0, le=1.0, description="BGM 볼륨")

    # 발행 설정
    publish_schedule: Optional[str] = Field(None, description="발행 스케줄 (예: 매주 월,수,금 10:00)")
    auto_deploy: bool = Field(False, description="자동 배포 여부")

    # 상태
    status: CampaignStatus = Field(CampaignStatus.ACTIVE, description="캠페인 상태")


class CampaignCreate(CampaignBase):
    """캠페인 생성 요청"""
    pass


class CampaignUpdate(BaseModel):
    """캠페인 업데이트 요청 (부분 업데이트)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    concept_gender: Optional[ConceptGender] = None
    concept_tone: Optional[ConceptTone] = None
    concept_style: Optional[ConceptStyle] = None
    target_duration: Optional[int] = Field(None, ge=10, le=600)
    voice_id: Optional[str] = None
    voice_name: Optional[str] = None
    intro_video_url: Optional[str] = None
    intro_duration: Optional[int] = Field(None, ge=0, le=10)
    outro_video_url: Optional[str] = None
    outro_duration: Optional[int] = Field(None, ge=0, le=10)
    bgm_url: Optional[str] = None
    bgm_volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    publish_schedule: Optional[str] = None
    auto_deploy: Optional[bool] = None
    status: Optional[CampaignStatus] = None


class Campaign(CampaignBase):
    """캠페인 응답"""
    id: int = Field(..., description="캠페인 ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CampaignListResponse(BaseModel):
    """캠페인 목록 응답"""
    campaigns: list[Campaign]
    total: int
    page: int
    page_size: int


class ResourceUploadRequest(BaseModel):
    """리소스 업로드 요청"""
    resource_type: str = Field(..., description="리소스 타입 (intro, outro, bgm)")
    file_url: Optional[str] = Field(None, description="파일 URL (이미 업로드된 경우)")


class ResourceUploadResponse(BaseModel):
    """리소스 업로드 응답"""
    resource_type: str
    url: str
    public_id: str
    duration: Optional[float] = None
    format: Optional[str] = None
