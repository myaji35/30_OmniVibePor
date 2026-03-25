"""
ElevenLabs 크레딧 사전 체크 유틸리티 (E-2)

TTS/Voice Cloning 호출 전 잔여 크레딧을 확인하여
크레딧 소진 시 즉시 AppError(CREDIT_EXHAUSTED) 발생.
"""
import logging
import httpx
from functools import lru_cache
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.middleware.error_handler import AppError

logger   = logging.getLogger(__name__)
settings = get_settings()

# 캐시: 1분간 API 재호출 방지
_cache: dict = {"data": None, "fetched_at": None}
_CACHE_TTL = timedelta(minutes=1)

# 최소 허용 잔여 크레딧 (이 이하면 경고)
MIN_WARNING_CHARACTERS = 10_000   # 10,000자
MIN_ERROR_CHARACTERS   = 1_000    # 1,000자 이하면 차단


async def fetch_subscription_info() -> dict:
    """ElevenLabs 구독 정보 조회 (캐시 포함)"""
    now = datetime.utcnow()

    # 캐시 유효 시 재사용
    if _cache["data"] and _cache["fetched_at"]:
        if now - _cache["fetched_at"] < _CACHE_TTL:
            return _cache["data"]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()
            _cache["data"]       = data
            _cache["fetched_at"] = now
            return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise AppError("UNAUTHORIZED", "ElevenLabs API 키가 유효하지 않습니다.")
        logger.warning(f"ElevenLabs 구독 조회 실패: {e}")
        return {}
    except Exception as e:
        logger.warning(f"ElevenLabs 구독 조회 실패 (네트워크): {e}")
        return {}


async def check_elevenlabs_credits(required_chars: int = 500) -> dict:
    """
    TTS 호출 전 크레딧 사전 확인.

    Args:
        required_chars: 이번 요청에 필요한 예상 글자 수

    Returns:
        {"character_count": int, "character_limit": int, "remaining": int}

    Raises:
        AppError("CREDIT_EXHAUSTED"): 잔여 크레딧 부족
    """
    info = await fetch_subscription_info()
    if not info:
        # API 조회 실패 → fail-open (차단하지 않음)
        logger.warning("ElevenLabs 크레딧 조회 실패 — 사전 체크 건너뜀")
        return {}

    used  = info.get("character_count", 0)
    limit = info.get("character_limit", 0)
    remaining = max(0, limit - used)

    status = {
        "character_count": used,
        "character_limit": limit,
        "remaining":       remaining,
        "tier":            info.get("tier", "unknown"),
    }

    # 잔여가 요청량보다 적으면 차단
    if limit > 0 and remaining < required_chars:
        logger.error(
            f"ElevenLabs 크레딧 부족: 필요={required_chars}, 잔여={remaining}"
        )
        raise AppError(
            "CREDIT_EXHAUSTED",
            f"ElevenLabs 크레딧이 부족합니다. "
            f"잔여 {remaining:,}자 / 필요 {required_chars:,}자. "
            f"ElevenLabs 대시보드에서 플랜을 업그레이드하세요.",
        )

    # 잔여량 경고 (차단은 안 함)
    if remaining < MIN_WARNING_CHARACTERS:
        logger.warning(
            f"ElevenLabs 크레딧 경고: 잔여 {remaining:,}자 "
            f"(임계값: {MIN_WARNING_CHARACTERS:,}자)"
        )

    return status


def get_estimated_chars(text: str) -> int:
    """텍스트 → 예상 소모 글자 수 (약 1.1배 여유)"""
    return int(len(text) * 1.1)
