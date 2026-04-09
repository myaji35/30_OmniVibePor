"""
ResourceLibrary 모델 — 캠페인별 자산 라이브러리 (이미지/영상/오디오)

실 스키마는 frontend/data/omnivibe.db의 resource_library 테이블 참조.
Phase 0-A Stage 2에서 sqlite3로 실제 컬럼 추출 후 상세 업데이트 예정.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResourceLibrary(Base):
    """캠페인별 자산 (이미지/영상/오디오)."""

    __tablename__ = "resource_library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Phase 0-A Stage 2에서 전체 컬럼 추가 예정
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ResourceLibrary id={self.id} campaign_id={self.campaign_id} type={self.type}>"
