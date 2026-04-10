"""
Tenancy Middleware — ISS-036 Phase 0-E

모든 DB 세션에 app.current_agency_id 변수를 주입하여
RLS 정책이 자동으로 테넌트 격리를 수행하도록 한다.

Usage:
    # main.py에서 미들웨어 등록
    from app.middleware.tenancy import TenancyMiddleware
    app.add_middleware(TenancyMiddleware)

    # 세션에서는 RLS가 자동 적용되어 agency_id 필터링 불필요
    async with get_session() as session:
        result = await session.execute(select(Client))
        # → agency_id = current_setting('app.current_agency_id') 조건 자동 적용

현재 구현:
    MVP 단계에서는 agency_id=1 고정 (싱글 테넌트).
    Phase 0-E Stage 2에서 JWT 토큰 → agency_id 추출로 전환.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 현재 요청의 agency_id를 ContextVar로 관리 (비동기 안전)
current_agency_id: ContextVar[Optional[int]] = ContextVar("current_agency_id", default=None)


class TenancyMiddleware(BaseHTTPMiddleware):
    """
    요청마다 agency_id를 추출하여 ContextVar에 설정.

    추출 우선순위:
    1. JWT 토큰의 agency_id claim (Phase 0-E Stage 2)
    2. X-Agency-Id 헤더 (개발/테스트용)
    3. 기본값 1 (MVP 싱글 테넌트)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # MVP: 고정 agency_id=1
        # TODO Phase 0-E Stage 2: JWT에서 추출
        agency_id = _extract_agency_id(request)
        token = current_agency_id.set(agency_id)

        try:
            response = await call_next(request)
            return response
        finally:
            current_agency_id.reset(token)


def _extract_agency_id(request: Request) -> int:
    """요청에서 agency_id 추출. MVP는 헤더 또는 기본값."""
    # 1. X-Agency-Id 헤더 (개발용)
    header_val = request.headers.get("X-Agency-Id")
    if header_val:
        try:
            return int(header_val)
        except (ValueError, TypeError):
            pass

    # 2. TODO: JWT 토큰에서 추출
    # auth_header = request.headers.get("Authorization")
    # if auth_header and auth_header.startswith("Bearer "):
    #     token = auth_header[7:]
    #     payload = decode_jwt(token)
    #     return payload.get("agency_id", 1)

    # 3. 기본값
    return 1


def get_current_agency_id() -> int:
    """현재 요청의 agency_id 반환. ContextVar에서 읽음."""
    return current_agency_id.get() or 1


async def set_pg_agency_id(conn, agency_id: int):
    """
    PostgreSQL 세션에 app.current_agency_id 변수 설정.
    RLS 정책이 이 변수를 참조하여 테넌트 격리 수행.

    Usage:
        async with engine.connect() as conn:
            await set_pg_agency_id(conn, agency_id)
            # 이후 쿼리는 RLS 자동 적용
    """
    from sqlalchemy import text
    await conn.execute(text(f"SET app.current_agency_id = '{agency_id}'"))
