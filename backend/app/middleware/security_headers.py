"""
Security Headers Middleware

OWASP 권장 보안 헤더 추가
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 자동 추가 Middleware
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        모든 응답에 보안 헤더 추가

        Args:
            request: FastAPI Request
            call_next: 다음 Middleware

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # 1. X-Content-Type-Options
        # - MIME 스니핑 방지
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. X-Frame-Options
        # - Clickjacking 공격 방지
        response.headers["X-Frame-Options"] = "DENY"

        # 3. X-XSS-Protection
        # - XSS 공격 방지 (레거시 브라우저 지원)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict-Transport-Security (HSTS)
        # - HTTPS 강제 (프로덕션에서만)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 5. Content-Security-Policy (CSP)
        # - XSS, 데이터 주입 공격 방지
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.omnivibepro.com wss://api.omnivibepro.com",
            "media-src 'self' https://res.cloudinary.com blob:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # 6. Referrer-Policy
        # - Referrer 정보 제한
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy (Feature-Policy 후속)
        # - 브라우저 기능 제한
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=(self)",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # 8. X-Permitted-Cross-Domain-Policies
        # - Adobe Flash/PDF 정책
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. Cache-Control (민감한 데이터)
        if request.url.path.startswith("/api/v1/auth") or \
           request.url.path.startswith("/api/v1/billing"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


def setup_security_headers(app):
    """
    FastAPI 앱에 Security Headers Middleware 추가

    Args:
        app: FastAPI 앱 인스턴스
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("✓ Security headers middleware enabled")


# CORS 정책 강화
ALLOWED_ORIGINS = [
    "https://omnivibepro.com",
    "https://www.omnivibepro.com",
    "https://studio.omnivibepro.com",
    "https://api.omnivibepro.com",
]

# 개발 환경
ALLOWED_ORIGINS_DEV = [
    "http://localhost:3020",
    "http://localhost:8000",
    "http://127.0.0.1:3020",
    "http://127.0.0.1:8000",
]


def get_allowed_origins(debug: bool = False) -> list:
    """
    환경에 따른 CORS Origin 반환

    Args:
        debug: Debug 모드 여부

    Returns:
        허용된 Origin 리스트
    """
    if debug:
        return ALLOWED_ORIGINS + ALLOWED_ORIGINS_DEV
    return ALLOWED_ORIGINS


# 보안 설정 검증
def validate_security_config():
    """
    보안 설정 검증 (프로덕션 배포 전 체크)

    Raises:
        ValueError: 보안 설정이 올바르지 않은 경우
    """
    import os

    errors = []

    # 1. SECRET_KEY 길이 확인
    secret_key = os.getenv("SECRET_KEY", "")
    if len(secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")

    # 2. DEBUG 모드 확인 (프로덕션)
    if os.getenv("ENV") == "production" and os.getenv("DEBUG", "false").lower() == "true":
        errors.append("DEBUG mode must be disabled in production")

    # 3. HTTPS 확인
    if os.getenv("ENV") == "production" and not os.getenv("FORCE_HTTPS", "false").lower() == "true":
        errors.append("HTTPS must be enforced in production")

    # 4. API 키 존재 확인
    required_keys = [
        "ELEVENLABS_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "STRIPE_SECRET_KEY",
    ]

    for key in required_keys:
        if not os.getenv(key):
            errors.append(f"{key} is not set")

    if errors:
        raise ValueError(
            f"Security configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    logger.info("✓ Security configuration validated")
