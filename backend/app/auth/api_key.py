"""API 키 인증"""
from typing import Optional
from fastapi import Header, HTTPException, status, Security
from fastapi.security import APIKeyHeader
import hashlib
from datetime import datetime

from app.models.user import APIKeyCRUD
from app.services.neo4j_client import Neo4jClient

# API 키 헤더 스키마
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Neo4j 클라이언트
neo4j_client = Neo4jClient()
api_key_crud = APIKeyCRUD(neo4j_client)


def hash_api_key(api_key: str) -> str:
    """
    API 키 해싱 (SHA-256)

    Args:
        api_key: 원본 API 키

    Returns:
        해시된 API 키
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_user_from_api_key(api_key: str) -> Optional[dict]:
    """
    API 키로 사용자 조회

    Args:
        api_key: API 키 문자열

    Returns:
        사용자 정보 또는 None
    """
    # API 키 해싱
    key_hash = hash_api_key(api_key)

    # DB에서 API 키 조회
    api_key_data = api_key_crud.get_api_key_by_hash(key_hash)

    if not api_key_data:
        return None

    # API 키 활성화 확인
    if not api_key_data.get("is_active", False):
        return None

    # 만료 시간 확인
    expires_at = api_key_data.get("expires_at")
    if expires_at and datetime.utcnow() > expires_at:
        return None

    # 사용 기록 업데이트
    api_key_crud.update_api_key_usage(api_key_data["key_id"])

    # 사용자 정보 반환
    return {
        "user_id": api_key_data["user_id"],
        "api_key_id": api_key_data["key_id"],
        "rate_limit": api_key_data.get("rate_limit", 1000),
    }


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> dict:
    """
    API 키 검증 의존성

    Args:
        api_key: X-API-Key 헤더 값

    Returns:
        사용자 정보

    Raises:
        HTTPException: 401 - API 키가 유효하지 않음

    Example:
        @app.get("/api/data", dependencies=[Depends(verify_api_key)])
        async def get_data():
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # API 키로 사용자 조회
    user = get_user_from_api_key(api_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user


async def get_optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[dict]:
    """
    선택적 API 키 검증

    API 키가 있으면 검증, 없으면 None 반환

    Args:
        api_key: X-API-Key 헤더 값

    Returns:
        사용자 정보 또는 None
    """
    if not api_key:
        return None

    user = get_user_from_api_key(api_key)
    return user


def check_api_key_rate_limit(api_key_id: str, limit: int = 1000) -> bool:
    """
    API 키별 Rate Limit 확인

    Args:
        api_key_id: API 키 ID
        limit: 시간당 요청 제한

    Returns:
        True (허용) / False (거부)
    """
    import redis
    from app.core.config import get_settings

    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    key = f"api_key_rate_limit:{api_key_id}"

    try:
        current = redis_client.get(key)

        if current is None:
            # 첫 요청
            redis_client.setex(key, 3600, 1)  # 1시간
            return True

        current_count = int(current)
        if current_count >= limit:
            # 제한 초과
            return False

        # 카운트 증가
        redis_client.incr(key)
        return True

    except Exception as e:
        # Redis 오류 시 허용
        print(f"API key rate limit check error: {e}")
        return True
