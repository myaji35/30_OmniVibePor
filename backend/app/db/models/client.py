"""
Client 모델 — 에이전시의 거래처 (병원/학원/마트 등)

실 스키마 (frontend/data/omnivibe.db):
    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand_color TEXT,
        logo_url TEXT,
        industry TEXT,
        contact_email TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

Phase 0-F 확장 (ISS-036 Phase 0-F):
    - agency_id: Integer, NOT NULL, FK to agencies.id
    - vertical: Literal['medical','academy','mart',...] (industry 대체)
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.campaign import Campaign


class Client(Base):
    """거래처 (에이전시가 서비스하는 최종 고객)."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand_color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # ISS-085 Stage 2: 브랜드 추출 컬럼
    website_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    extract_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extract_raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Phase 0-E/F: tenancy
    agency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name!r} industry={self.industry!r}>"
