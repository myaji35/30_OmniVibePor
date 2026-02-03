"""A/B 테스트 모델

A/B 테스트는 동일한 스크립트에 대한 여러 변형을 생성하고,
각 변형의 성과를 비교하여 최적의 버전을 찾는 기능입니다.

구조:
- ContentSchedule (1) -> ABTest (N)
- 각 ABTest는 variant_name으로 구분 (A, B, C...)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ABTestBase(BaseModel):
    """A/B 테스트 기본 모델"""
    content_id: int = Field(..., description="콘텐츠 ID (content_schedule)")
    variant_name: str = Field(..., min_length=1, max_length=50, description="변형 이름 (A, B, C...)")
    script_version: Optional[str] = Field(None, description="스크립트 버전 (전체 텍스트)")
    audio_url: Optional[str] = Field(None, description="생성된 오디오 URL (Cloudinary)")
    video_url: Optional[str] = Field(None, description="생성된 비디오 URL (Cloudinary)")


class ABTestCreate(ABTestBase):
    """A/B 테스트 생성 요청"""
    pass


class ABTestUpdate(BaseModel):
    """A/B 테스트 업데이트 요청 (부분 업데이트)"""
    script_version: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None


class ABTestTrackRequest(BaseModel):
    """A/B 테스트 성과 기록 요청"""
    views: int = Field(..., ge=0, description="조회수")
    engagement_rate: float = Field(..., ge=0.0, le=100.0, description="참여율 (%)")


class ABTest(ABTestBase):
    """A/B 테스트 응답"""
    id: int = Field(..., description="A/B 테스트 ID")
    views: int = Field(0, description="조회수")
    engagement_rate: float = Field(0.0, description="참여율 (%)")
    created_at: datetime = Field(..., description="생성 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ABTestListResponse(BaseModel):
    """A/B 테스트 목록 응답"""
    tests: list[ABTest]
    total: int


class ABTestComparisonResponse(BaseModel):
    """A/B 테스트 비교 응답"""
    content_id: int
    tests: list[ABTest]
    best_variant: Optional[str] = Field(None, description="최고 성과 변형")
    best_engagement: float = Field(0.0, description="최고 참여율")
