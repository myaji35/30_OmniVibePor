"""
ContentSchedule 모델 — 캠페인 내 개별 콘텐츠 일정

실 스키마:
    CREATE TABLE content_schedule (
        id INTEGER PRIMARY KEY,
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        topic TEXT NOT NULL,
        subtitle TEXT NOT NULL,
        platform TEXT NOT NULL CHECK(platform IN ('Youtube','Instagram','TikTok','Facebook')),
        publish_date DATE,
        status TEXT DEFAULT 'draft' CHECK(status IN ('draft','scheduled','published','archived')),
        target_audience TEXT,
        keywords TEXT,
        notes TEXT,
        script_data TEXT,
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
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.campaign import Campaign
    from app.db.models.generated_script import GeneratedScript
    from app.db.models.storyboard_block import StoryboardBlock


class ContentSchedule(Base):
    """콘텐츠 일정 (캠페인당 여러 개)."""

    __tablename__ = "content_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String, nullable=False)
    subtitle: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    publish_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
            "platform IN ('Youtube', 'Instagram', 'TikTok', 'Facebook')",
            name="ck_content_schedule_platform",
        ),
        CheckConstraint(
            "status IN ('draft', 'scheduled', 'published', 'archived')",
            name="ck_content_schedule_status",
        ),
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="content_schedules")
    generated_scripts: Mapped[List["GeneratedScript"]] = relationship(
        "GeneratedScript",
        back_populates="content",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    storyboard_blocks: Mapped[List["StoryboardBlock"]] = relationship(
        "StoryboardBlock",
        back_populates="content",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<ContentSchedule id={self.id} topic={self.topic!r} status={self.status}>"
