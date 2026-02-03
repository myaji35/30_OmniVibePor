"""JWT 토큰 생성 및 검증"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import redis
from app.core.config import get_settings

settings = get_settings()

# JWT 설정
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

# Redis 클라이언트 (토큰 블랙리스트)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    액세스 토큰 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id, email, role 등)
        expires_delta: 만료 시간 (기본값: 30분)

    Returns:
        JWT 액세스 토큰
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    리프레시 토큰 생성

    Args:
        data: 토큰에 포함할 데이터 (user_id만 포함 권장)

    Returns:
        JWT 리프레시 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    토큰 검증 및 디코딩

    Args:
        token: JWT 토큰
        token_type: 토큰 타입 ("access" 또는 "refresh")

    Returns:
        디코딩된 토큰 데이터 또는 None (검증 실패 시)
    """
    try:
        # 블랙리스트 확인
        if is_token_blacklisted(token):
            return None

        # 토큰 디코딩
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # 토큰 타입 확인
        if payload.get("type") != token_type:
            return None

        return payload

    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    토큰 디코딩 (검증 없이)

    Args:
        token: JWT 토큰

    Returns:
        디코딩된 토큰 데이터 또는 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except JWTError:
        return None


def blacklist_token(token: str) -> bool:
    """
    토큰을 블랙리스트에 추가 (로그아웃 시 사용)

    Args:
        token: 블랙리스트에 추가할 JWT 토큰

    Returns:
        성공 여부
    """
    try:
        # 토큰 디코딩하여 만료 시간 확인
        payload = decode_token(token)
        if not payload:
            return False

        exp = payload.get("exp")
        if not exp:
            return False

        # 만료 시간까지 Redis에 저장
        expire_time = datetime.fromtimestamp(exp)
        ttl = int((expire_time - datetime.utcnow()).total_seconds())

        if ttl > 0:
            redis_client.setex(f"blacklist:{token}", ttl, "1")

        return True

    except Exception:
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    토큰이 블랙리스트에 있는지 확인

    Args:
        token: 확인할 JWT 토큰

    Returns:
        블랙리스트 포함 여부
    """
    try:
        return redis_client.exists(f"blacklist:{token}") > 0
    except Exception:
        return False


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    토큰 만료 시간 조회

    Args:
        token: JWT 토큰

    Returns:
        만료 시간 (datetime) 또는 None
    """
    payload = decode_token(token)
    if not payload or "exp" not in payload:
        return None

    return datetime.fromtimestamp(payload["exp"])
