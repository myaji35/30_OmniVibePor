"""
SQLAlchemy 2.0 Async Base — ISS-036 Phase 0-A (옵션 A, PostgreSQL 풀 마이그)

역할:
    기존 raw aiosqlite 기반 sqlite_client.py와 병렬로, SQLAlchemy 2.0 async ORM 레이어를 도입한다.
    Phase 0-A 동안은 SQLite 파일을 그대로 쓰고(DATABASE_URL=sqlite+aiosqlite://...),
    Phase 0-C/0-D에서 PostgreSQL(DATABASE_URL=postgresql+asyncpg://...)로 환경변수만 전환한다.

설계 원칙:
    1. DeclarativeBase — 모든 모델이 상속
    2. async engine + async_sessionmaker — FastAPI 의존성에서 세션 주입
    3. SQLite/PostgreSQL 양방향 호환 — DATABASE_URL 하나로 전환
    4. 기존 sqlite_client.py는 그대로 유지 — 점진적 교체 (Phase 0-A Stage 2~3)
    5. Phase 0-E에서 tenancy ContextVar + RLS 변수 주입이 이 세션 레이어를 확장

Usage:
    from app.db.base import async_session_factory, Base
    from app.db.models.campaign import Campaign

    async with async_session_factory() as session:
        result = await session.execute(select(Campaign).where(Campaign.id == 1))
        campaign = result.scalar_one_or_none()

환경변수:
    DATABASE_URL — 기본값: sqlite+aiosqlite://{frontend/data/omnivibe.db}
    DB_ECHO — True면 SQL 로그 출력 (기본 False)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE_URL 결정
# ─────────────────────────────────────────────────────────────────────────────

# 기존 sqlite_client.py의 DB_PATH 로직을 그대로 승계
# Phase 0-A/B: SQLite (현재 위치)
# Phase 0-C/D: PostgreSQL (DATABASE_URL 환경변수로 전환)
DEFAULT_SQLITE_PATH = (
    Path(__file__).parent.parent.parent.parent / "frontend" / "data" / "omnivibe.db"
)


def get_database_url() -> str:
    """DATABASE_URL 환경변수 또는 기본 SQLite 경로 반환."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        logger.info(f"Using DATABASE_URL from env: {env_url.split('@')[-1] if '@' in env_url else env_url}")
        return env_url

    sqlite_url = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"
    logger.info(f"Using default SQLite: {DEFAULT_SQLITE_PATH}")
    return sqlite_url


DATABASE_URL = get_database_url()
DB_ECHO = os.environ.get("DB_ECHO", "false").lower() == "true"


# ─────────────────────────────────────────────────────────────────────────────
# DeclarativeBase
# ─────────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 DeclarativeBase — 모든 모델의 루트.

    이 Base를 상속하는 모델은 Alembic autogenerate가 자동 인식하며,
    Phase 0-B에서 Alembic 초기 migration 생성 시 사용된다.
    """
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Async Engine + Session Factory
# ─────────────────────────────────────────────────────────────────────────────

def _create_engine() -> AsyncEngine:
    """
    Async engine 생성.

    SQLite용 설정:
        - check_same_thread=False (async 필수)
        - URI mode 사용

    PostgreSQL 용 설정:
        - connection pool (asyncpg 기본값)
        - statement_cache_size=0 (개발 시 스키마 변경 빈번)
    """
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif DATABASE_URL.startswith("postgresql"):
        # Phase 0-B~C에서 PostgreSQL 전환 시 적용
        connect_args = {}

    engine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,  # 끊어진 커넥션 자동 재연결
    )
    return engine


# 단일 engine 인스턴스 (모듈 로드 시 1회 생성)
engine: AsyncEngine = _create_engine()

# Async session factory
# expire_on_commit=False — FastAPI 의존성 패턴에서 session 종료 후에도 객체 접근 가능
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Dependency
# ─────────────────────────────────────────────────────────────────────────────

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 — 요청마다 새 session 생성.

    사용 예:
        from fastapi import Depends
        from app.db.base import get_db_session
        from sqlalchemy.ext.asyncio import AsyncSession

        @router.get("/items/{id}")
        async def get_item(id: int, db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item).where(Item.id == id))
            return result.scalar_one_or_none()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─────────────────────────────────────────────────────────────────────────────
# 초기화 헬퍼 (Phase 0-B 이후 사용)
# ─────────────────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    DB 초기화 — 개발/테스트 용.

    프로덕션에서는 Alembic migration 사용.
    Phase 0-B 이후 이 함수는 호출하지 말 것 (Alembic이 관리).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB tables created via init_db() — DEV ONLY")


async def dispose_engine() -> None:
    """
    엔진 종료 — 앱 shutdown 시 호출.

    사용 예 (main.py):
        @app.on_event("shutdown")
        async def shutdown():
            await dispose_engine()
    """
    await engine.dispose()
    logger.info("Database engine disposed")


__all__ = [
    "Base",
    "engine",
    "async_session_factory",
    "get_db_session",
    "init_db",
    "dispose_engine",
    "DATABASE_URL",
]
