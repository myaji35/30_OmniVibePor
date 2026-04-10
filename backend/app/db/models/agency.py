"""
Agency + AgencyMember 모델 — ISS-036 Phase 0-E/F

Agency: 1인 마케팅 에이전시 (SaaS 테넌트 단위)
AgencyMember: 에이전시 소속 멤버 (추후 멀티유저 확장용)

RLS 정책:
    모든 테넌트 격리 테이블에 agency_id FK → RLS USING (agency_id = current_setting('app.current_agency_id')::int)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Agency(Base):
    """1인 마케팅 에이전시 (SaaS 테넌트)."""

    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(String, default="free", nullable=False)
    # 향후 ISS-085 Firecrawl 온보딩에서 채움
    website_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Agency id={self.id} name={self.name!r} plan={self.plan}>"


class AgencyMember(Base):
    """에이전시 소속 멤버."""

    __tablename__ = "agency_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agency_id: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="owner", nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgencyMember id={self.id} agency_id={self.agency_id} role={self.role}>"
