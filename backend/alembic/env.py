"""
Alembic env.py — ISS-089 Phase 0-B

Async migration runner for SQLAlchemy 2.0 + PostgreSQL (asyncpg).
Falls back to SQLite (aiosqlite) via DATABASE_URL env var.
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# sys.path에 backend/ 추가 (모델 import)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 모든 모델 import (autogenerate가 테이블을 인식하도록)
from app.db.base import Base  # noqa: E402
from app.db.models.client import Client  # noqa: E402,F401
from app.db.models.campaign import Campaign  # noqa: E402,F401
from app.db.models.content_schedule import ContentSchedule  # noqa: E402,F401
from app.db.models.generated_script import GeneratedScript  # noqa: E402,F401
from app.db.models.storyboard_block import StoryboardBlock  # noqa: E402,F401
from app.db.models.resource_library import ResourceLibrary  # noqa: E402,F401
from app.db.models.ab_test import AbTest  # noqa: E402,F401
from app.db.models.agency import Agency, AgencyMember  # noqa: E402,F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# DATABASE_URL 환경변수로 오버라이드
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
