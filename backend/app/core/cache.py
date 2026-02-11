"""
In-memory caching layer with TTL support.
Reduces database queries for frequently accessed data like schema introspection.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Get current UTC time in timezone-aware format."""
    return datetime.now(timezone.utc)


@dataclass
class CacheEntry:
    """A single cache entry with value and expiration."""

    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=_utc_now)

    @property
    def is_expired(self) -> bool:
        return _utc_now() > self.expires_at


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.

    Features:
    - TTL-based expiration
    - Automatic cleanup of expired entries
    - Key prefixing for namespacing
    - Cache statistics
    """

    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize the cache.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = json.dumps(
            {"args": [str(a) for a in args], "kwargs": kwargs}, sort_keys=True
        )
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if not found or expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Set a value in cache with optional custom TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = _utc_now() + timedelta(seconds=ttl)
        async with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (prefix match)."""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        async with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }


# Global cache instance
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        from app.config import get_settings

        settings = get_settings()
        _cache = InMemoryCache(default_ttl_seconds=settings.cache_ttl_seconds)
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
