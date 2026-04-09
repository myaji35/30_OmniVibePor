"""
Campaign 모델 — 거래처의 영상 마케팅 캠페인

실 스키마 (frontend/data/omnivibe.db):
    CREATE TABLE campaigns (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        client_id INTEGER REFERENCES clients(id),
        start_date DATE,
        end_date DATE,
        status TEXT DEFAULT 'active' CHECK(status IN ('active','paused','completed')),
        concept_gender TEXT, concept_tone TEXT, concept_style TEXT,
        target_duration INTEGER,
        voice_id TEXT, voice_name TEXT,
        intro_video_url TEXT, intro_duration INTEGER DEFAULT 5,
        outro_video_url TEXT, outro_duration INTEGER DEFAULT 5,
        bgm_url TEXT, bgm_volume REAL DEFAULT 0.3,
        publish_schedule TEXT, auto_deploy INTEGER DEFAULT 0,
        created_at, updated_at
    );
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.client import Client
    from app.db.models.content_schedule import ContentSchedule


class Campaign(Base):
    """영상 마케팅 캠페인 (거래처당 여러 개)."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)

    # Concept settings
    concept_gender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    concept_tone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    concept_style: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Voice settings
    voice_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    voice_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Intro/outro settings
    intro_video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    intro_duration: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    outro_video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    outro_duration: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # BGM settings
    bgm_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bgm_volume: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)

    # Publishing settings
    publish_schedule: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    auto_deploy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'completed')",
            name="ck_campaigns_status",
        ),
    )

    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="campaigns")
    content_schedules: Mapped[List["ContentSchedule"]] = relationship(
        "ContentSchedule",
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} name={self.name!r} status={self.status}>"
