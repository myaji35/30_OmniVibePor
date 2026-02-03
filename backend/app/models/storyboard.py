"""Storyboard 관련 Pydantic 모델"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VisualConcept(BaseModel):
    """비주얼 컨셉 모델"""
    mood: str = Field(..., description="분위기 (energetic, calm, serious, playful)")
    color_tone: str = Field(..., description="색감 (bright, dark, warm, cool)")
    background_style: str = Field(..., description="배경 스타일 (modern, vintage, natural, abstract)")
    background_prompt: str = Field(..., description="DALL-E 프롬프트 (영문, 50자 이내)")
    transition_from_previous: str = Field(..., description="이전 블록으로부터 전환 효과 (fade, slide, dissolve, zoom)")


class StoryboardBlock(BaseModel):
    """콘티 블록 모델"""
    id: Optional[int] = Field(None, description="블록 ID (DB 저장 후 생성)")
    order: int = Field(..., description="블록 순서 (0부터 시작)")
    script: str = Field(..., description="스크립트 텍스트")
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    keywords: List[str] = Field(default_factory=list, description="핵심 키워드 리스트")
    visual_concept: VisualConcept = Field(..., description="비주얼 컨셉")
    background_type: str = Field(
        ...,
        description="배경 타입 (uploaded, ai_generated, stock, solid_color)"
    )
    background_url: Optional[str] = Field(None, description="배경 이미지/영상 URL")
    background_prompt: Optional[str] = Field(None, description="AI 생성 프롬프트")
    transition_effect: str = Field(..., description="전환 효과 (fade, slide, dissolve, zoom)")
    subtitle_preset: str = Field(default="normal", description="자막 프리셋 (normal, bold, italic)")


class CampaignConcept(BaseModel):
    """캠페인 컨셉 모델"""
    gender: str = Field(..., description="성별 (male, female, neutral)")
    tone: str = Field(..., description="톤 (professional, casual, energetic, calm)")
    style: str = Field(..., description="스타일 (modern, classic, creative, formal)")
    target_audience: Optional[str] = Field(None, description="타겟 오디언스")
    platform: Optional[str] = Field(None, description="플랫폼 (YouTube, Instagram, TikTok)")


class GenerateStoryboardRequest(BaseModel):
    """콘티 블록 자동 생성 요청"""
    script: str = Field(..., description="스크립트 전체 텍스트")
    campaign_concept: CampaignConcept = Field(..., description="캠페인 컨셉")
    target_duration: int = Field(
        default=180,
        ge=15,
        le=600,
        description="목표 영상 길이 (초, 15~600초)"
    )


class GenerateStoryboardResponse(BaseModel):
    """콘티 블록 자동 생성 응답"""
    success: bool = Field(..., description="성공 여부")
    storyboard_blocks: List[StoryboardBlock] = Field(
        default_factory=list,
        description="생성된 콘티 블록 리스트"
    )
    total_blocks: int = Field(..., description="총 블록 수")
    estimated_duration: float = Field(..., description="예상 영상 길이 (초)")
    error: Optional[str] = Field(None, description="에러 메시지 (실패 시)")


class StoryboardBlockUpdate(BaseModel):
    """콘티 블록 수정 요청"""
    script: Optional[str] = None
    keywords: Optional[List[str]] = None
    visual_concept: Optional[VisualConcept] = None
    background_type: Optional[str] = None
    background_url: Optional[str] = None
    background_prompt: Optional[str] = None
    transition_effect: Optional[str] = None
    subtitle_preset: Optional[str] = None


class BackgroundSuggestion(BaseModel):
    """배경 추천 모델"""
    type: str = Field(..., description="타입 (ai_generated, stock, solid_color)")
    priority: int = Field(..., description="우선순위 (1이 가장 높음)")
    prompt: Optional[str] = Field(None, description="AI 생성 프롬프트")
    search_keywords: Optional[List[str]] = Field(None, description="스톡 검색 키워드")
    color_hex: Optional[str] = Field(None, description="단색 배경 색상 (hex)")
    rationale: str = Field(..., description="추천 이유")
