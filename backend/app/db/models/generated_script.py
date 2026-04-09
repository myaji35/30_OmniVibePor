"""
GeneratedScript 모델 — AI가 생성한 영상 스크립트 (Hook/Body/CTA 구조)

실 스키마:
    CREATE TABLE generated_scripts (
        id INTEGER PRIMARY KEY,
        content_id INTEGER NOT NULL REFERENCES content_schedule(id) ON DELETE CASCADE,
        hook TEXT NOT NULL,
        body TEXT NOT NULL,
        cta TEXT NOT NULL,
        total_duration INTEGER,  -- 초 단위
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.content_schedule import ContentSchedule


class GeneratedScript(Base):
    """AI 생성 스크립트 (Hook + Body + CTA)."""

    __tablename__ = "generated_scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content_schedule.id", ondelete="CASCADE"), nullable=False
    )
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    total_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    content: Mapped["ContentSchedule"] = relationship(
        "ContentSchedule", back_populates="generated_scripts"
    )

    def __repr__(self) -> str:
        return f"<GeneratedScript id={self.id} content_id={self.content_id} duration={self.total_duration}s>"
