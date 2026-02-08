"""Redis 캐싱 서비스

API 응답 및 데이터베이스 쿼리 결과를 캐싱하여 성능 향상
"""
import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
import redis
from datetime import timedelta

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """Redis 기반 캐싱 서비스"""

    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.default_ttl = 300  # 5분

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        # args와 kwargs를 문자열로 변환
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

        # 해시 생성 (긴 키 방지)
        if key_parts:
            key_hash = hashlib.md5(
                "".join(key_parts).encode()
            ).hexdigest()[:12]
            return f"{prefix}:{key_hash}"
        else:
            return prefix

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"✅ Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"❌ Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """캐시에 값 저장"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """캐시 삭제"""
        try:
            deleted = self.redis_client.delete(key)
            if deleted:
                logger.debug(f"🗑️  Cache DELETE: {key}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 여러 캐시 삭제"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️  Cache DELETE PATTERN: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0

    def flush_all(self) -> bool:
        """전체 캐시 삭제 (주의!)"""
        try:
            self.redis_client.flushdb()
            logger.warning("⚠️  All cache flushed!")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False

    def get_stats(self) -> dict:
        """캐시 통계"""
        try:
            info = self.redis_client.info('stats')
            return {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "total_keys": self.redis_client.dbsize()
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

    def _calculate_hit_rate(self, info: dict) -> float:
        """Hit rate 계산"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# 싱글톤 인스턴스
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """CacheService 싱글톤"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ==================== 데코레이터 ====================

def cached(
    prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        prefix: 캐시 키 prefix
        ttl: Time-to-live (초)
        key_builder: 커스텀 키 생성 함수

    Example:
        @cached(prefix="script", ttl=600)
        def get_script(campaign_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # 캐시 키 생성
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)

            # 캐시 확인
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 함수 실행
            result = func(*args, **kwargs)

            # 캐시 저장
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def async_cached(
    prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    비동기 함수용 캐싱 데코레이터

    Example:
        @async_cached(prefix="neo4j:scripts", ttl=600)
        async def search_similar_scripts(platform: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # 캐시 키 생성
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)

            # 캐시 확인
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 함수 실행
            result = await func(*args, **kwargs)

            # 캐시 저장
            if result is not None:
                cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# ==================== 캐시 무효화 헬퍼 ====================

def invalidate_campaign_cache(campaign_id: int):
    """캠페인 관련 캐시 무효화"""
    cache = get_cache_service()
    cache.delete_pattern(f"campaign:{campaign_id}:*")
    cache.delete_pattern(f"script:{campaign_id}:*")
    logger.info(f"Campaign {campaign_id} cache invalidated")


def invalidate_content_cache(content_id: int):
    """콘텐츠 관련 캐시 무효화"""
    cache = get_cache_service()
    cache.delete_pattern(f"content:{content_id}:*")
    logger.info(f"Content {content_id} cache invalidated")


def invalidate_writer_cache():
    """Writer Agent 캐시 무효화"""
    cache = get_cache_service()
    cache.delete_pattern("writer:*")
    cache.delete_pattern("neo4j:*")
    logger.info("Writer cache invalidated")
