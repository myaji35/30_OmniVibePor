"""Rate Limiting 미들웨어"""
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from app.core.config import get_settings

settings = get_settings()

# Redis 클라이언트
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# SlowAPI Limiter 초기화
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],
    storage_uri=settings.REDIS_URL,
)


def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    요청에서 user_id 추출 (JWT 토큰 또는 API 키)

    Args:
        request: FastAPI Request 객체

    Returns:
        user_id 또는 None
    """
    # Authorization 헤더에서 JWT 토큰 추출
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # JWT 디코딩하여 user_id 추출
        from app.auth.jwt_handler import decode_token
        payload = decode_token(token)
        if payload:
            return payload.get("sub")

    # API 키 헤더 확인
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # API 키로 user_id 조회
        from app.auth.api_key import get_user_from_api_key
        user = get_user_from_api_key(api_key)
        if user:
            return user.get("user_id")

    return None


async def check_rate_limit(
    request: Request,
    limit: int,
    window: int = 3600
) -> bool:
    """
    Rate limit 확인

    Args:
        request: FastAPI Request 객체
        limit: 요청 제한 횟수
        window: 시간 윈도우 (초, 기본값: 1시간)

    Returns:
        True (허용) / False (거부)
    """
    # User ID 또는 IP 주소 기반 키 생성
    user_id = get_user_id_from_request(request)
    if user_id:
        key = f"rate_limit:user:{user_id}:{request.url.path}"
    else:
        client_ip = request.client.host
        key = f"rate_limit:ip:{client_ip}:{request.url.path}"

    try:
        # Redis에서 현재 카운트 조회
        current = redis_client.get(key)

        if current is None:
            # 첫 요청
            redis_client.setex(key, window, 1)
            return True

        current_count = int(current)
        if current_count >= limit:
            # 제한 초과
            return False

        # 카운트 증가
        redis_client.incr(key)
        return True

    except Exception as e:
        # Redis 오류 시 허용 (fail-open)
        print(f"Rate limit check error: {e}")
        return True


def get_rate_limit_headers(request: Request, limit: int, window: int = 3600) -> dict:
    """
    Rate limit 헤더 생성

    Args:
        request: FastAPI Request 객체
        limit: 요청 제한 횟수
        window: 시간 윈도우 (초)

    Returns:
        Rate limit 헤더 딕셔너리
    """
    user_id = get_user_id_from_request(request)
    if user_id:
        key = f"rate_limit:user:{user_id}:{request.url.path}"
    else:
        client_ip = request.client.host
        key = f"rate_limit:ip:{client_ip}:{request.url.path}"

    try:
        current = redis_client.get(key)
        remaining = limit - int(current) if current else limit
        ttl = redis_client.ttl(key)

        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(ttl) if ttl > 0 else str(window),
        }
    except Exception:
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(limit),
            "X-RateLimit-Reset": str(window),
        }


# 엔드포인트별 Rate Limit 설정
ENDPOINT_RATE_LIMITS = {
    "/api/v1/audio/generate": {"limit": 10, "window": 3600},  # 10 req/hour
    "/api/v1/presentations/generate-video": {"limit": 5, "window": 3600},  # 5 req/hour
    "/api/v1/voice/clone": {"limit": 5, "window": 3600},  # 5 req/hour
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting 미들웨어"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 전 Rate Limit 확인

        Args:
            request: FastAPI Request
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response

        Raises:
            HTTPException: 429 - Rate limit exceeded
        """
        # 엔드포인트별 제한 확인
        path = request.url.path
        rate_limit_config = ENDPOINT_RATE_LIMITS.get(path)

        if rate_limit_config:
            limit = rate_limit_config["limit"]
            window = rate_limit_config["window"]

            # Rate limit 확인
            allowed = await check_rate_limit(request, limit, window)

            if not allowed:
                # Rate limit headers 추가
                headers = get_rate_limit_headers(request, limit, window)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window // 3600} hour(s).",
                    headers=headers,
                )

        # 요청 처리
        response = await call_next(request)

        # Rate limit headers 추가
        if rate_limit_config:
            headers = get_rate_limit_headers(
                request,
                rate_limit_config["limit"],
                rate_limit_config["window"]
            )
            for key, value in headers.items():
                response.headers[key] = value

        return response


# 미들웨어 인스턴스
rate_limit_middleware = RateLimitMiddleware
