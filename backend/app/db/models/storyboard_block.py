"""
StoryboardBlock 모델 — 영상의 씬 단위 블록

실 스키마:
    CREATE TABLE storyboard_blocks (
        id INTEGER PRIMARY KEY,
        content_id INTEGER NOT NULL REFERENCES content_schedule(id) ON DELETE CASCADE,
        block_number INTEGER,
        type TEXT,
        start_time REAL, end_time REAL, duration REAL,
        script TEXT, audio_url TEXT,
        background_type TEXT, background_url TEXT, background_source TEXT,
        character_enabled INTEGER DEFAULT 0, character_url TEXT,
        character_start REAL, character_duration REAL,
        subtitle_text TEXT, subtitle_preset TEXT, subtitle_position TEXT DEFAULT 'bottom',
        transition_effect TEXT, transition_duration REAL DEFAULT 0.5,
        created_at, updated_at
    );
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.content_schedule import ContentSchedule


class StoryboardBlock(Base):
    """스토리보드 블록 (영상의 개별 씬)."""

    __tablename__ = "storyboard_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content_schedule.id", ondelete="CASCADE"), nullable=False
    )
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Background
    background_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    background_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    background_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Character
    character_enabled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    character_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    character_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    character_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Subtitle
    subtitle_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subtitle_preset: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subtitle_position: Mapped[str] = mapped_column(String, default="bottom", nullable=False)

    # Transition
    transition_effect: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transition_duration: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    content: Mapped["ContentSchedule"] = relationship(
        "ContentSchedule", back_populates="storyboard_blocks"
    )

    def __repr__(self) -> str:
        return f"<StoryboardBlock id={self.id} block_number={self.block_number} type={self.type}>"
