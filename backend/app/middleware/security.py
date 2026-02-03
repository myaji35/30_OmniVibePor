"""보안 헤더 미들웨어"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 추가 미들웨어

    OWASP 권장 보안 헤더를 자동으로 추가합니다.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        모든 응답에 보안 헤더 추가

        Args:
            request: FastAPI Request
            call_next: 다음 미들웨어/핸들러

        Returns:
            보안 헤더가 추가된 Response
        """
        response = await call_next(request)

        # Content Security Policy (CSP)
        # 스크립트, 스타일, 이미지 등의 로드 소스 제한
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self' https://api.openai.com https://api.elevenlabs.io; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # X-Frame-Options
        # 클릭재킹(Clickjacking) 방지
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        # MIME 타입 스니핑 방지
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        # XSS 필터 활성화 (레거시 브라우저 지원)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security (HSTS)
        # HTTPS 강제 (프로덕션 환경에서만)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer-Policy
        # 리퍼러 정보 제어
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (Feature-Policy)
        # 브라우저 기능 접근 제어
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # X-Permitted-Cross-Domain-Policies
        # 크로스 도메인 정책 제한 (Adobe Flash 등)
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Cache-Control (민감한 데이터)
        # 인증 관련 엔드포인트는 캐시 금지
        if "/auth/" in request.url.path or "/api-keys" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Server 헤더 제거 (서버 정보 은닉)
        response.headers["Server"] = "OmniVibe-Pro"

        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    CORS 보안 강화 미들웨어

    개발 환경과 프로덕션 환경에서 다른 CORS 정책 적용
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        CORS 헤더 검증 및 추가

        Args:
            request: FastAPI Request
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response
        """
        response = await call_next(request)

        # 프로덕션 환경: 특정 도메인만 허용
        if not settings.DEBUG:
            allowed_origins = [
                "https://omnivibepro.com",
                "https://app.omnivibepro.com",
            ]

            origin = request.headers.get("origin")
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
            else:
                # 허용되지 않은 Origin은 헤더 제거
                response.headers.pop("Access-Control-Allow-Origin", None)

        return response
