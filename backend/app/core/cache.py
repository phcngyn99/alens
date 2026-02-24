"""
Redis caching layer with TTL support.
Reduces database queries for frequently accessed data like schema introspection.
"""

import json
import logging
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        from app.config import get_settings

        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


class RedisCache:
    """
    Redis-based cache with TTL support.

    Features:
    - TTL-based expiration (handled by Redis)
    - Pattern-based key deletion
    - Persistent across restarts
    - Shared across multiple backend instances
    """

    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize the cache.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 5 minutes)
        """
        self._default_ttl = default_ttl_seconds

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if not found or expired."""
        try:
            client = await get_redis()
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Set a value in cache with optional custom TTL."""
        try:
            client = await get_redis()
            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl

            # Properly serialize Pydantic models to dictionaries
            serializable_value = self._to_serializable(value)
            serialized = json.dumps(serializable_value, default=str)
            await client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Redis set error for key {key}: {e}")

    def _to_serializable(self, value: Any) -> Any:
        """Convert value to a JSON-serializable format, handling Pydantic models."""
        if isinstance(value, BaseModel):
            # Pydantic v2: use model_dump() to convert to dict
            return value.model_dump()
        elif isinstance(value, list):
            return [self._to_serializable(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._to_serializable(v) for k, v in value.items()}
        else:
            return value

    async def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        try:
            client = await get_redis()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (prefix match)."""
        try:
            client = await get_redis()
            # Use SCAN to find matching keys (safer than KEYS for large datasets)
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await client.scan(cursor, match=f"{pattern}*", count=100)
                if keys:
                    deleted_count += await client.delete(*keys)
                if cursor == 0:
                    break
            return deleted_count
        except Exception as e:
            logger.warning(f"Redis delete_pattern error for pattern {pattern}: {e}")
            return 0

    async def clear(self) -> None:
        """Clear all cache entries with 'conn:' prefix (our namespace)."""
        try:
            await self.delete_pattern("conn:")
        except Exception as e:
            logger.warning(f"Redis clear error: {e}")

    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            client = await get_redis()
            await client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        from app.config import get_settings

        settings = get_settings()
        _cache = RedisCache(default_ttl_seconds=settings.cache_ttl_seconds)
    return _cache


# Cache key prefixes
class CacheKeys:
    """Cache key prefixes for different data types."""

    SCHEMAS = "schemas"
    TABLES = "tables"
    TABLE_DETAIL = "table_detail"
    SCHEMA_DETAIL = "schema_detail"
    TABLE_PREVIEW = "table_preview"
    CONNECTION = "connection"

    @staticmethod
    def for_connection(connection_id: UUID) -> str:
        """Get prefix for all cache entries related to a connection."""
        return f"conn:{connection_id}"

    @staticmethod
    def schemas(connection_id: UUID) -> str:
        return f"conn:{connection_id}:schemas"

    @staticmethod
    def tables(connection_id: UUID, schema_name: str) -> str:
        return f"conn:{connection_id}:schema:{schema_name}:tables"

    @staticmethod
    def schema_detail(
        connection_id: UUID, schema_name: str, include_stats: bool
    ) -> str:
        return f"conn:{connection_id}:schema:{schema_name}:detail:{include_stats}"

    @staticmethod
    def table_detail(connection_id: UUID, schema_name: str, table_name: str) -> str:
        return f"conn:{connection_id}:schema:{schema_name}:table:{table_name}"

    @staticmethod
    def table_preview(
        connection_id: UUID, schema_name: str, table_name: str, limit: int
    ) -> str:
        return f"conn:{connection_id}:schema:{schema_name}:table:{table_name}:preview:{limit}"
