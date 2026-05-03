import os
import time
from typing import Optional

try:
    import redis
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False

CACHE_TTL = int(os.environ.get("RESPONSE_CACHE_TTL", "300"))


class InMemoryCache:
    def __init__(self):
        self.store = {}

    def get(self, key: str) -> Optional[str]:
        item = self.store.get(key)
        if not item:
            return None
        value, expires = item
        if expires < time.time():
            del self.store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int = CACHE_TTL):
        self.store[key] = (value, time.time() + ttl)


class ResponseCache:
    """
    Response cache with graceful Redis fallback.

    Priority:
      1. Redis (if REDIS_URL is set and connection is alive)
      2. In-memory dict (always available, silent fallback)

    On any Redis ConnectionError / Error 10061, silently switches to
    InMemoryCache without spamming logs. This prevents Redis outages from
    crashing or slowing down the chatbot pipeline.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self._redis_url = redis_url or os.environ.get("REDIS_URL")
        self._redis_available = False
        self._client: Optional[object] = None
        self._memory = InMemoryCache()
        self._connect_redis()

    def _connect_redis(self) -> None:
        """Try to connect to Redis. Fail silently on ConnectionError."""
        if not _REDIS_AVAILABLE or not self._redis_url:
            self._redis_available = False
            return

        try:
            self._client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            # Quick health check — ping() raises ConnectionError on Error 10061
            self._client.ping()
            self._redis_available = True
            print(f"[ResponseCache] Redis connected: {self._redis_url}")
        except Exception as exc:
            # Error 10061 = connection refused, host unreachable, etc.
            # Silently fall back to in-memory — no log spam.
            self._redis_available = False
            self._client = None
            print(f"[ResponseCache] Redis unavailable ({exc}), using in-memory cache")

    def _ensure_redis(self) -> None:
        """
        Re-check Redis connectivity if currently unavailable.
        Called lazily on each get/set to avoid blocking startup.
        """
        if not self._redis_available and self._redis_url:
            self._connect_redis()

    # ── public API ────────────────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[str]:
        # Try Redis first if alive
        if self._redis_available and self._client is not None:
            try:
                return self._client.get(key)
            except Exception:
                # Redis died between check and call — fall back silently
                self._redis_available = False
                self._client = None
        # Fall through to in-memory
        return self._memory.get(key)

    def set(self, key: str, value: str, ttl: int = CACHE_TTL) -> None:
        if self._redis_available and self._client is not None:
            try:
                self._client.set(key, value, ex=ttl)
                return
            except Exception:
                # Redis died — fall back silently
                self._redis_available = False
                self._client = None
        self._memory.set(key, value, ttl)
