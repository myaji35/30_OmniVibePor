"""Security Middleware - Rate Limiting & API Key Authentication"""
import time
import hashlib
from typing import Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers

from app.core.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting Middleware"""

    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 허용 호출 수
        self.period = period  # 기간 (초)
        self.clients = defaultdict(list)  # IP별 요청 기록

    async def dispatch(self, request: Request, call_next: Callable):
        # Health check는 제외
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # 클라이언트 IP 추출
        client_ip = request.client.host

        # 현재 시간
        now = time.time()

        # 오래된 기록 삭제 (메모리 절약)
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < self.period
        ]

        # Rate limit 체크
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Max {self.calls} requests per {self.period} seconds.",
                    "retry_after": int(self.period - (now - self.clients[client_ip][0]))
                }
            )

        # 요청 기록
        self.clients[client_ip].append(now)

        # 다음 미들웨어로
        response = await call_next(request)
        
        # Rate limit 헤더 추가
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(now + self.period)
        )

        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key Authentication Middleware"""

    def __init__(
        self,
        app,
        api_key_header: str = "X-API-Key",
        exempt_paths: list[str] = None
    ):
        super().__init__(app)
        self.api_key_header = api_key_header
        self.exempt_paths = exempt_paths or [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        # 프로덕션에서는 환경 변수나 DB에서 로드
        self.valid_api_keys = self._load_api_keys()

    def _load_api_keys(self) -> set[str]:
        """API 키 로드 (환경 변수 또는 DB)"""
        # 개발 환경용 기본 키
        default_keys = {
            hashlib.sha256("dev_key_123".encode()).hexdigest()
        }
        # 프로덕션에서는 DB나 Redis에서 로드
        return default_keys

    async def dispatch(self, request: Request, call_next: Callable):
        # 제외 경로 체크
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # API Key 추출
        api_key = request.headers.get(self.api_key_header)

        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Missing API Key",
                    "detail": f"API Key required in '{self.api_key_header}' header"
                }
            )

        # API Key 검증
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if api_key_hash not in self.valid_api_keys:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Invalid API Key",
                    "detail": "The provided API Key is invalid"
                }
            )

        # 다음 미들웨어로
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security Headers Middleware"""

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        # Security Headers 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


def get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출 (Proxy 고려)"""
    # X-Forwarded-For 헤더 확인 (Nginx, Cloudflare 등)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 직접 연결
    return request.client.host
