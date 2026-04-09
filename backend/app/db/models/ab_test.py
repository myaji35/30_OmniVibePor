"""
AbTest 모델 — A/B 테스트 variant 추적

실 스키마 (backend/omni_db.sqlite, 별도 DB):
    CREATE TABLE ab_tests (
        id INTEGER PRIMARY KEY,
        content_id INTEGER NOT NULL,
        variant_name TEXT NOT NULL,
        script_version TEXT,
        audio_url TEXT, video_url TEXT,
        views INTEGER DEFAULT 0,
        engagement_rate REAL DEFAULT 0.0,
        created_at TEXT DEFAULT (datetime('now'))
    );

Note:
    현재 backend DB는 별도 파일 (backend/omni_db.sqlite).
    Phase 0-C에서 PostgreSQL 전환 시 단일 DB로 통합됨.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AbTest(Base):
    """A/B 테스트 variant."""

    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False)
    variant_name: Mapped[str] = mapped_column(String, nullable=False)
    script_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AbTest id={self.id} content_id={self.content_id} "
            f"variant={self.variant_name!r} views={self.views}>"
        )
