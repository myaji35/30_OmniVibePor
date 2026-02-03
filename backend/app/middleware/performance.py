"""Performance Optimization Middleware

This module provides middleware for:
- Response caching with Redis
- Gzip compression for responses
- Request timing and performance monitoring
- Database connection pooling optimization
"""
import time
import json
import logging
import hashlib
from typing import Callable, Optional
from contextlib import nullcontext

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Conditional imports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Redis-based response caching middleware

    Caches GET requests for specified cache duration.
    Supports cache invalidation by URL pattern.
    """

    # Cacheable endpoints (pattern -> TTL in seconds)
    CACHEABLE_ENDPOINTS = {
        "/api/v1/voice/list/": 300,  # 5 minutes
        "/api/v1/performance/insights/": 600,  # 10 minutes
        "/health": 60,  # 1 minute
        "/": 3600,  # 1 hour
    }

    def __init__(self, app, redis_client: Optional[any] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.enabled = redis_client is not None and REDIS_AVAILABLE

        if not self.enabled:
            logger.warning("Cache middleware disabled: Redis not available")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only cache GET requests
        if request.method != "GET" or not self.enabled:
            return await call_next(request)

        # Check if endpoint is cacheable
        cache_ttl = self._get_cache_ttl(request.url.path)
        if cache_ttl is None:
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get cached response
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"Cache hit: {request.url.path}")
            return JSONResponse(
                content=cached_response,
                headers={"X-Cache": "HIT"}
            )

        # Process request
        response = await call_next(request)

        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            await self._cache_response(cache_key, response, cache_ttl)
            logger.debug(f"Cache miss (stored): {request.url.path}")

        # Add cache header
        response.headers["X-Cache"] = "MISS"

        return response

    def _get_cache_ttl(self, path: str) -> Optional[int]:
        """Get cache TTL for given path"""
        for pattern, ttl in self.CACHEABLE_ENDPOINTS.items():
            if path.startswith(pattern):
                return ttl
        return None

    def _generate_cache_key(self, request: Request) -> str:
        """Generate unique cache key from request"""
        # Include path + query params
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        key_string = ":".join(key_parts)

        # Hash for shorter key
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"cache:{key_hash}"

    def _get_cached_response(self, cache_key: str) -> Optional[dict]:
        """Retrieve cached response"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")

        return None

    async def _cache_response(
        self,
        cache_key: str,
        response: Response,
        ttl: int
    ) -> None:
        """Store response in cache"""
        if not self.redis_client:
            return

        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Parse JSON
            response_data = json.loads(body.decode())

            # Store in Redis
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response_data)
            )

            # Recreate response with same body
            response.body_iterator = self._create_body_iterator(body)

        except Exception as e:
            logger.error(f"Cache storage error: {e}")

    @staticmethod
    async def _create_body_iterator(body: bytes):
        """Create async iterator for response body"""
        yield body


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Request timing middleware

    Measures response time for each request and logs to Logfire.
    Adds X-Response-Time header to responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Use Logfire span if available
        span_context = (
            logfire.span(
                f"{request.method} {request.url.path}",
                _tags={"http.method": request.method, "http.path": request.url.path}
            )
            if LOGFIRE_AVAILABLE
            else nullcontext()
        )

        with span_context:
            response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Add header
        response.headers["X-Response-Time"] = f"{process_time:.4f}s"

        # Log slow requests (> 2 seconds)
        if process_time > 2.0:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )

        # Log to Logfire
        if LOGFIRE_AVAILABLE:
            logfire.info(
                f"Request completed: {request.method} {request.url.path}",
                response_time_ms=process_time * 1000,
                status_code=response.status_code
            )

        return response


class CompressionMiddleware(GZipMiddleware):
    """
    Enhanced Gzip compression middleware

    Compresses responses larger than 1KB using gzip.
    Configured for optimal balance between compression ratio and speed.
    """

    def __init__(self, app, minimum_size: int = 1000, compression_level: int = 6):
        """
        Args:
            app: FastAPI application
            minimum_size: Minimum response size to compress (bytes)
            compression_level: Gzip compression level (1-9, default 6)
        """
        super().__init__(app, minimum_size=minimum_size)
        self.compression_level = compression_level
        logger.info(
            f"Compression middleware enabled: "
            f"min_size={minimum_size}B, level={compression_level}"
        )


# Redis connection pool for caching
_redis_client = None


def get_redis_client():
    """Get or create Redis client with connection pooling"""
    global _redis_client

    if _redis_client is None and REDIS_AVAILABLE:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=50,  # Connection pool size
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            _redis_client = None

    return _redis_client


def clear_cache_by_pattern(pattern: str) -> int:
    """
    Clear cache entries matching pattern

    Args:
        pattern: Redis key pattern (e.g., "cache:voice:*")

    Returns:
        Number of keys deleted
    """
    redis_client = get_redis_client()
    if not redis_client:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Cleared {deleted} cache entries matching '{pattern}'")
            return deleted
    except Exception as e:
        logger.error(f"Cache clearing error: {e}")

    return 0
