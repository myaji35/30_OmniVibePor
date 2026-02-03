"""Client Pydantic Models

클라이언트 관리를 위한 Pydantic 모델 정의
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class ClientBase(BaseModel):
    """클라이언트 기본 정보"""
    name: str = Field(..., min_length=1, max_length=200, description="클라이언트 이름")
    brand_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="브랜드 컬러 (Hex)")
    logo_url: Optional[str] = Field(None, description="로고 URL")
    industry: Optional[str] = Field(None, max_length=100, description="산업 분야")
    contact_email: Optional[EmailStr] = Field(None, description="담당자 이메일")


class ClientCreate(ClientBase):
    """클라이언트 생성 요청"""
    pass


class ClientUpdate(BaseModel):
    """클라이언트 수정 요청 (Partial Update)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="클라이언트 이름")
    brand_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="브랜드 컬러 (Hex)")
    logo_url: Optional[str] = Field(None, description="로고 URL")
    industry: Optional[str] = Field(None, max_length=100, description="산업 분야")
    contact_email: Optional[EmailStr] = Field(None, description="담당자 이메일")


class Client(ClientBase):
    """클라이언트 응답 모델"""
    client_id: str = Field(..., description="클라이언트 고유 ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ClientModel(BaseModel):
    """클라이언트 Neo4j 모델 (내부용)"""
    client_id: str = Field(
        default_factory=lambda: f"client_{uuid.uuid4().hex[:12]}"
    )
    name: str
    brand_color: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
