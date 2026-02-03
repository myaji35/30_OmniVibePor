"""Performance Monitoring Service

This module tracks and reports:
- API endpoint response times
- Celery task execution times
- FFmpeg rendering times
- Export metrics to Logfire
"""
import time
import logging
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import nullcontext

# Conditional imports
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str  # Metric name (e.g., "api.generate_video")
    duration_ms: float  # Duration in milliseconds
    timestamp: str  # ISO format timestamp
    status: str  # "success" or "failed"
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class PerformanceMonitor:
    """
    Performance monitoring service

    Features:
    - Track operation durations
    - Store metrics in Redis
    - Export to Logfire
    - Generate performance reports
    """

    # Metric retention period (7 days)
    RETENTION_DAYS = 7

    # Metric categories
    CATEGORY_API = "api"
    CATEGORY_TASK = "task"
    CATEGORY_FFMPEG = "ffmpeg"
    CATEGORY_DATABASE = "database"

    def __init__(self, redis_client: Optional[any] = None):
        self.redis_client = redis_client
        self.enabled = redis_client is not None and REDIS_AVAILABLE

        # In-memory fallback storage
        self.metrics_buffer: List[PerformanceMetric] = []
        self.max_buffer_size = 1000

        if not self.enabled:
            logger.warning(
                "Performance monitoring using in-memory buffer "
                "(Redis not available)"
            )
        else:
            logger.info("Performance monitoring enabled with Redis storage")

    def track(
        self,
        category: str = CATEGORY_API,
        include_metadata: bool = False
    ) -> Callable:
        """
        Decorator to track function execution time

        Args:
            category: Metric category (api/task/ffmpeg/database)
            include_metadata: Include function arguments in metadata

        Usage:
            @performance_monitor.track(category="api")
            async def generate_video(...):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                error = None

                # Use Logfire span if available
                span_context = (
                    logfire.span(
                        f"{category}.{func.__name__}",
                        _tags={"category": category}
                    )
                    if LOGFIRE_AVAILABLE
                    else nullcontext()
                )

                try:
                    with span_context:
                        result = await func(*args, **kwargs)
                    return result

                except Exception as e:
                    status = "failed"
                    error = str(e)
                    raise

                finally:
                    # Calculate duration
                    duration_ms = (time.time() - start_time) * 1000

                    # Build metadata
                    metadata = {"category": category}
                    if include_metadata:
                        metadata["args"] = str(args)[:100]  # Truncate
                        metadata["kwargs"] = str(kwargs)[:100]
                    if error:
                        metadata["error"] = error

                    # Record metric
                    self.record(
                        name=f"{category}.{func.__name__}",
                        duration_ms=duration_ms,
                        status=status,
                        metadata=metadata
                    )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                error = None

                span_context = (
                    logfire.span(
                        f"{category}.{func.__name__}",
                        _tags={"category": category}
                    )
                    if LOGFIRE_AVAILABLE
                    else nullcontext()
                )

                try:
                    with span_context:
                        result = func(*args, **kwargs)
                    return result

                except Exception as e:
                    status = "failed"
                    error = str(e)
                    raise

                finally:
                    duration_ms = (time.time() - start_time) * 1000

                    metadata = {"category": category}
                    if include_metadata:
                        metadata["args"] = str(args)[:100]
                        metadata["kwargs"] = str(kwargs)[:100]
                    if error:
                        metadata["error"] = error

                    self.record(
                        name=f"{category}.{func.__name__}",
                        duration_ms=duration_ms,
                        status=status,
                        metadata=metadata
                    )

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def record(
        self,
        name: str,
        duration_ms: float,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a performance metric

        Args:
            name: Metric name (e.g., "api.generate_video")
            duration_ms: Duration in milliseconds
            status: "success" or "failed"
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            name=name,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            status=status,
            metadata=metadata or {}
        )

        # Store in Redis if available
        if self.enabled:
            self._store_metric_redis(metric)
        else:
            # Store in memory buffer
            self._store_metric_buffer(metric)

        # Log to Logfire
        if LOGFIRE_AVAILABLE:
            logfire.info(
                f"Performance metric: {name}",
                duration_ms=duration_ms,
                status=status,
                **metadata
            )

        # Log slow operations
        if duration_ms > 2000:  # > 2 seconds
            logger.warning(
                f"Slow operation: {name} took {duration_ms:.0f}ms "
                f"(status: {status})"
            )

    def get_metrics(
        self,
        category: Optional[str] = None,
        hours: int = 24
    ) -> List[PerformanceMetric]:
        """
        Retrieve metrics from storage

        Args:
            category: Filter by category (api/task/ffmpeg/database)
            hours: Time window in hours (default 24)

        Returns:
            List of performance metrics
        """
        if self.enabled:
            return self._get_metrics_redis(category, hours)
        else:
            return self._get_metrics_buffer(category, hours)

    def generate_report(
        self,
        category: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate performance report

        Args:
            category: Filter by category
            hours: Time window in hours

        Returns:
            Performance statistics
        """
        metrics = self.get_metrics(category, hours)

        if not metrics:
            return {
                "period_hours": hours,
                "category": category,
                "total_operations": 0,
                "message": "No metrics available"
            }

        # Calculate statistics
        durations = [m.duration_ms for m in metrics]
        successful = [m for m in metrics if m.status == "success"]
        failed = [m for m in metrics if m.status == "failed"]

        # Group by operation name
        by_operation = defaultdict(list)
        for metric in metrics:
            by_operation[metric.name].append(metric.duration_ms)

        operation_stats = {}
        for name, durations_list in by_operation.items():
            operation_stats[name] = {
                "count": len(durations_list),
                "avg_ms": sum(durations_list) / len(durations_list),
                "min_ms": min(durations_list),
                "max_ms": max(durations_list),
                "p95_ms": self._percentile(durations_list, 95),
                "p99_ms": self._percentile(durations_list, 99)
            }

        report = {
            "period_hours": hours,
            "category": category or "all",
            "total_operations": len(metrics),
            "successful_operations": len(successful),
            "failed_operations": len(failed),
            "success_rate": len(successful) / len(metrics) * 100,
            "overall_stats": {
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p50_duration_ms": self._percentile(durations, 50),
                "p95_duration_ms": self._percentile(durations, 95),
                "p99_duration_ms": self._percentile(durations, 99)
            },
            "by_operation": operation_stats
        }

        return report

    def clear_metrics(self, category: Optional[str] = None) -> int:
        """
        Clear stored metrics

        Args:
            category: Clear specific category (or all if None)

        Returns:
            Number of metrics cleared
        """
        if self.enabled:
            return self._clear_metrics_redis(category)
        else:
            return self._clear_metrics_buffer(category)

    # Redis storage methods

    def _store_metric_redis(self, metric: PerformanceMetric) -> None:
        """Store metric in Redis with TTL"""
        try:
            # Use sorted set with timestamp as score
            key = f"perf:{metric.name}"
            score = datetime.fromisoformat(metric.timestamp).timestamp()

            # Store metric data
            self.redis_client.zadd(
                key,
                {str(asdict(metric)): score}
            )

            # Set expiration (7 days)
            self.redis_client.expire(key, self.RETENTION_DAYS * 86400)

        except Exception as e:
            logger.error(f"Failed to store metric in Redis: {e}")

    def _get_metrics_redis(
        self,
        category: Optional[str],
        hours: int
    ) -> List[PerformanceMetric]:
        """Retrieve metrics from Redis"""
        try:
            # Calculate time window
            cutoff_time = (
                datetime.utcnow() - timedelta(hours=hours)
            ).timestamp()

            # Get all metric keys
            pattern = f"perf:{category}.*" if category else "perf:*"
            keys = self.redis_client.keys(pattern)

            metrics = []
            for key in keys:
                # Get metrics within time window
                raw_metrics = self.redis_client.zrangebyscore(
                    key, cutoff_time, "+inf"
                )

                for raw_metric in raw_metrics:
                    # Parse metric data
                    metric_dict = eval(raw_metric)  # Safe since we control the data
                    metrics.append(PerformanceMetric(**metric_dict))

            return metrics

        except Exception as e:
            logger.error(f"Failed to retrieve metrics from Redis: {e}")
            return []

    def _clear_metrics_redis(self, category: Optional[str]) -> int:
        """Clear metrics from Redis"""
        try:
            pattern = f"perf:{category}.*" if category else "perf:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} metric keys from Redis")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Failed to clear metrics from Redis: {e}")
            return 0

    # In-memory buffer methods

    def _store_metric_buffer(self, metric: PerformanceMetric) -> None:
        """Store metric in memory buffer"""
        self.metrics_buffer.append(metric)

        # Limit buffer size
        if len(self.metrics_buffer) > self.max_buffer_size:
            # Remove oldest metrics
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]

    def _get_metrics_buffer(
        self,
        category: Optional[str],
        hours: int
    ) -> List[PerformanceMetric]:
        """Retrieve metrics from memory buffer"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_metrics = [
            m for m in self.metrics_buffer
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]

        if category:
            filtered_metrics = [
                m for m in filtered_metrics
                if m.name.startswith(f"{category}.")
            ]

        return filtered_metrics

    def _clear_metrics_buffer(self, category: Optional[str]) -> int:
        """Clear metrics from memory buffer"""
        if category:
            original_count = len(self.metrics_buffer)
            self.metrics_buffer = [
                m for m in self.metrics_buffer
                if not m.name.startswith(f"{category}.")
            ]
            cleared = original_count - len(self.metrics_buffer)
        else:
            cleared = len(self.metrics_buffer)
            self.metrics_buffer = []

        return cleared

    # Utility methods

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Singleton instance
_performance_monitor_instance = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get PerformanceMonitor singleton instance"""
    global _performance_monitor_instance

    if _performance_monitor_instance is None:
        # Try to get Redis client
        redis_client = None
        if REDIS_AVAILABLE:
            try:
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=3,  # Separate DB for metrics
                    decode_responses=True,
                    socket_timeout=5
                )
                redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis unavailable for metrics: {e}")
                redis_client = None

        _performance_monitor_instance = PerformanceMonitor(redis_client)

    return _performance_monitor_instance
