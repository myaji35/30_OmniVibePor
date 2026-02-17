"""
Rate Limiting Middleware

slowapi를 사용한 API Rate Limiting
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Limiter 인스턴스 생성
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # 기본 제한
    storage_uri="redis://localhost:6379/1",  # Redis 사용 (선택사항)
)


def setup_rate_limiting(app):
    """
    FastAPI 앱에 Rate Limiting 설정

    Args:
        app: FastAPI 앱 인스턴스
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.info("✓ Rate limiting enabled")


# 엔드포인트별 Rate Limit 설정
RATE_LIMITS = {
    # 인증 (브루트 포스 방지)
    "/api/v1/auth/login": "5/minute",
    "/api/v1/auth/register": "3/hour",
    "/api/v1/auth/refresh": "10/minute",

    # AI 생성 (비용 많이 드는 작업)
    "/api/v1/writer/generate": "10/minute",
    "/api/v1/audio/generate": "20/minute",
    "/api/v1/video/render": "5/minute",

    # 일반 API
    "/api/v1/campaigns": "100/minute",
    "/api/v1/contents": "100/minute",

    # Billing (민감한 작업)
    "/api/v1/billing/subscriptions": "5/minute",
    "/api/v1/billing/checkout": "3/minute",
}


def get_rate_limit(path: str) -> str:
    """
    경로에 따른 Rate Limit 반환

    Args:
        path: API 경로

    Returns:
        Rate limit 문자열 (예: "5/minute")
    """
    for endpoint, limit in RATE_LIMITS.items():
        if path.startswith(endpoint):
            return limit

    # 기본 제한
    return "200/minute"


# 커스텀 Rate Limit 핸들러
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Rate Limit 초과 시 커스텀 응답

    Args:
        request: FastAPI Request
        exc: RateLimitExceeded 예외

    Returns:
        HTTPException (429)
    """
    logger.warning(
        f"Rate limit exceeded for {request.client.host} "
        f"on {request.url.path}"
    )

    return HTTPException(
        status_code=429,
        detail={
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail.split("Retry in ")[1] if "Retry in" in exc.detail else "60 seconds"
        }
    )


# IP 기반 차단 리스트 (선택사항)
BLOCKED_IPS = set()


def is_ip_blocked(ip: str) -> bool:
    """
    IP가 차단 목록에 있는지 확인

    Args:
        ip: IP 주소

    Returns:
        차단 여부
    """
    return ip in BLOCKED_IPS


def block_ip(ip: str):
    """
    IP를 차단 목록에 추가

    Args:
        ip: 차단할 IP 주소
    """
    BLOCKED_IPS.add(ip)
    logger.warning(f"IP blocked: {ip}")


def unblock_ip(ip: str):
    """
    IP 차단 해제

    Args:
        ip: 차단 해제할 IP 주소
    """
    if ip in BLOCKED_IPS:
        BLOCKED_IPS.remove(ip)
        logger.info(f"IP unblocked: {ip}")
