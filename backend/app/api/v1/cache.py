"""Cache Management API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.cache_service import (
    get_cache_service,
    invalidate_campaign_cache,
    invalidate_content_cache,
    invalidate_writer_cache
)

router = APIRouter()
logger = logging.getLogger(__name__)


class CacheStatsResponse(BaseModel):
    """캐시 통계 응답"""
    keyspace_hits: int
    keyspace_misses: int
    hit_rate: float
    total_keys: int


class CacheInvalidateRequest(BaseModel):
    """캐시 무효화 요청"""
    pattern: Optional[str] = None
    campaign_id: Optional[int] = None
    content_id: Optional[int] = None


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    캐시 통계 조회

    **응답**:
    - keyspace_hits: 캐시 히트 수
    - keyspace_misses: 캐시 미스 수
    - hit_rate: 히트율 (%)
    - total_keys: 전체 캐시 키 수
    """
    cache = get_cache_service()
    stats = cache.get_stats()

    return CacheStatsResponse(
        keyspace_hits=stats.get("keyspace_hits", 0),
        keyspace_misses=stats.get("keyspace_misses", 0),
        hit_rate=stats.get("hit_rate", 0.0),
        total_keys=stats.get("total_keys", 0)
    )


@router.post("/invalidate")
async def invalidate_cache(request: CacheInvalidateRequest):
    """
    캐시 무효화

    **파라미터**:
    - pattern: 패턴 매칭 (예: "campaign:*")
    - campaign_id: 특정 캠페인 캐시 삭제
    - content_id: 특정 콘텐츠 캐시 삭제

    **사용 예시**:
    ```json
    {
      "campaign_id": 123
    }
    ```
    """
    cache = get_cache_service()

    if request.campaign_id:
        invalidate_campaign_cache(request.campaign_id)
        return {
            "status": "success",
            "message": f"Campaign {request.campaign_id} cache invalidated"
        }

    if request.content_id:
        invalidate_content_cache(request.content_id)
        return {
            "status": "success",
            "message": f"Content {request.content_id} cache invalidated"
        }

    if request.pattern:
        deleted = cache.delete_pattern(request.pattern)
        return {
            "status": "success",
            "message": f"Deleted {deleted} keys matching '{request.pattern}'"
        }

    raise HTTPException(
        status_code=400,
        detail="Must provide campaign_id, content_id, or pattern"
    )


@router.post("/flush")
async def flush_cache():
    """
    전체 캐시 삭제 (주의!)

    **경고**: 모든 캐시가 삭제됩니다.
    """
    cache = get_cache_service()
    cache.flush_all()

    return {
        "status": "success",
        "message": "All cache flushed"
    }


@router.delete("/{key}")
async def delete_cache_key(key: str):
    """
    특정 캐시 키 삭제

    **파라미터**:
    - key: 캐시 키
    """
    cache = get_cache_service()
    deleted = cache.delete(key)

    if deleted:
        return {
            "status": "success",
            "message": f"Cache key '{key}' deleted"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Cache key '{key}' not found"
        )
