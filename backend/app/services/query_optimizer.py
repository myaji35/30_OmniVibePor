"""Database Query Optimization Service

This module provides:
- Neo4j query caching
- Batch query execution
- Query profiling decorators
- Common query optimizations
"""
import logging
import hashlib
import json
import functools
import time
from typing import List, Dict, Any, Optional, Callable
from contextlib import nullcontext

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


class QueryOptimizer:
    """
    Query optimization service for Neo4j

    Features:
    - Query result caching with Redis
    - Batch query execution
    - Query profiling and logging
    """

    def __init__(self, redis_client: Optional[any] = None):
        self.redis_client = redis_client
        self.cache_enabled = redis_client is not None and REDIS_AVAILABLE

        if not self.cache_enabled:
            logger.warning("Query caching disabled: Redis not available")

    def cached_query(
        self,
        ttl: int = 300,
        key_prefix: str = "query"
    ) -> Callable:
        """
        Decorator for caching query results

        Args:
            ttl: Time to live in seconds (default 5 minutes)
            key_prefix: Cache key prefix

        Usage:
            @query_optimizer.cached_query(ttl=600)
            def get_user_data(user_id: str):
                return neo4j_client.execute_query(...)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = self._generate_cache_key(
                    key_prefix, func.__name__, args, kwargs
                )

                # Try to get cached result
                if self.cache_enabled:
                    cached_result = self._get_cached_result(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Query cache hit: {func.__name__}")
                        return cached_result

                # Execute query
                result = func(*args, **kwargs)

                # Cache result
                if self.cache_enabled and result is not None:
                    self._cache_result(cache_key, result, ttl)
                    logger.debug(f"Query cache miss (stored): {func.__name__}")

                return result

            return wrapper
        return decorator

    def profiled_query(self, func: Callable) -> Callable:
        """
        Decorator for profiling query execution time

        Usage:
            @query_optimizer.profiled_query
            def get_user_data(user_id: str):
                return neo4j_client.execute_query(...)
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Use Logfire span if available
            span_context = (
                logfire.span(
                    f"neo4j.{func.__name__}",
                    _tags={"query": func.__name__}
                )
                if LOGFIRE_AVAILABLE
                else nullcontext()
            )

            with span_context:
                result = func(*args, **kwargs)

            execution_time = time.time() - start_time

            # Log slow queries (> 1 second)
            if execution_time > 1.0:
                logger.warning(
                    f"Slow query detected: {func.__name__} "
                    f"took {execution_time:.2f}s"
                )
            else:
                logger.debug(
                    f"Query executed: {func.__name__} "
                    f"in {execution_time:.3f}s"
                )

            # Log to Logfire
            if LOGFIRE_AVAILABLE:
                logfire.info(
                    f"Neo4j query: {func.__name__}",
                    execution_time_ms=execution_time * 1000
                )

            return result

        return wrapper

    def batch_execute(
        self,
        neo4j_client: any,
        queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Execute multiple queries in a batch transaction

        Args:
            neo4j_client: Neo4j client instance
            queries: List of queries with format:
                [
                    {"query": "MATCH ...", "parameters": {...}},
                    {"query": "CREATE ...", "parameters": {...}},
                ]

        Returns:
            List of query results
        """
        logger.info(f"Executing batch of {len(queries)} queries")

        span_context = (
            logfire.span(f"neo4j.batch_execute", _tags={"count": len(queries)})
            if LOGFIRE_AVAILABLE
            else nullcontext()
        )

        with span_context:
            results = []

            # Execute queries in transaction
            with neo4j_client.driver.session() as session:
                with session.begin_transaction() as tx:
                    for query_dict in queries:
                        result = tx.run(
                            query_dict["query"],
                            query_dict.get("parameters", {})
                        )
                        results.append(list(result))

                    tx.commit()

        logger.info(f"Batch execution completed: {len(results)} results")
        return results

    def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cached queries matching pattern

        Args:
            pattern: Cache key pattern (e.g., "query:user:*")

        Returns:
            Number of keys deleted
        """
        if not self.cache_enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cached queries matching '{pattern}'")
                return deleted
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

        return 0

    def _generate_cache_key(
        self,
        prefix: str,
        func_name: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate unique cache key from function call"""
        key_parts = {
            "function": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_parts, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached query result"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")

        return None

    def _cache_result(self, cache_key: str, result: Any, ttl: int) -> None:
        """Store query result in cache"""
        if not self.redis_client:
            return

        try:
            # Convert result to JSON-serializable format
            serialized = json.dumps(result, default=str)
            self.redis_client.setex(cache_key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache storage error: {e}")


# Singleton instance
_query_optimizer_instance = None


def get_query_optimizer() -> QueryOptimizer:
    """Get QueryOptimizer singleton instance"""
    global _query_optimizer_instance

    if _query_optimizer_instance is None:
        # Try to get Redis client
        redis_client = None
        if REDIS_AVAILABLE:
            try:
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=2,  # Separate DB for query cache
                    decode_responses=True,
                    socket_timeout=5
                )
                redis_client.ping()
                logger.info("Query optimizer Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis unavailable for query caching: {e}")
                redis_client = None

        _query_optimizer_instance = QueryOptimizer(redis_client)

    return _query_optimizer_instance


# Common optimized queries for Neo4j

def create_indexes(neo4j_client: any) -> None:
    """
    Create recommended indexes for common queries

    Call this during application initialization.
    """
    logger.info("Creating Neo4j indexes for query optimization")

    indexes = [
        # User indexes
        "CREATE INDEX user_id_idx IF NOT EXISTS FOR (u:User) ON (u.user_id)",
        "CREATE INDEX user_email_idx IF NOT EXISTS FOR (u:User) ON (u.email)",

        # Presentation indexes
        "CREATE INDEX pres_id_idx IF NOT EXISTS FOR (p:Presentation) ON (p.presentation_id)",
        "CREATE INDEX pres_status_idx IF NOT EXISTS FOR (p:Presentation) ON (p.status)",
        "CREATE INDEX pres_user_idx IF NOT EXISTS FOR (p:Presentation) ON (p.user_id)",

        # Voice indexes
        "CREATE INDEX voice_id_idx IF NOT EXISTS FOR (v:Voice) ON (v.voice_id)",
        "CREATE INDEX voice_user_idx IF NOT EXISTS FOR (v:Voice) ON (v.user_id)",

        # Performance indexes
        "CREATE INDEX perf_platform_idx IF NOT EXISTS FOR (p:Performance) ON (p.platform)",
        "CREATE INDEX perf_date_idx IF NOT EXISTS FOR (p:Performance) ON (p.date)",
    ]

    try:
        for index_query in indexes:
            neo4j_client.execute_query(index_query)
            logger.debug(f"Created index: {index_query[:50]}...")

        logger.info("Neo4j indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


# Example optimized query patterns

class OptimizedQueries:
    """Collection of optimized Neo4j queries"""

    @staticmethod
    def get_user_presentations_optimized(
        neo4j_client: any,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Optimized query to get user presentations

        Uses:
        - Index on user_id
        - Limit to reduce result set
        - Only returns necessary fields
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[:CREATED]->(p:Presentation)
        RETURN p.presentation_id, p.title, p.status, p.created_at
        ORDER BY p.created_at DESC
        LIMIT $limit
        """

        result = neo4j_client.execute_query(
            query,
            parameters={"user_id": user_id, "limit": limit}
        )

        return result

    @staticmethod
    def get_presentation_details_optimized(
        neo4j_client: any,
        presentation_id: str
    ) -> Optional[Dict]:
        """
        Optimized query to get presentation details

        Uses:
        - Index on presentation_id
        - Single node match (no traversal)
        """
        query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        RETURN p
        LIMIT 1
        """

        result = neo4j_client.execute_query(
            query,
            parameters={"presentation_id": presentation_id}
        )

        return result[0] if result else None
