"""
Rate Limiting Middleware and Decorator
Hỗ trợ giới hạn truy vấn theo nhiều cấp: phút, giờ, ngày.
Sử dụng Redis với fallback in-memory (thread-safe).
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# In-memory fallback store (thread-safe, process-scoped)
# Used when Redis is unavailable (e.g., error 10061 connection refused).
# ──────────────────────────────────────────────────────────────────────────────

class _InMemoryCounter:
    """Thread-safe counter with automatic expiry."""

    __slots__ = ("value", "reset_at")

    def __init__(self) -> None:
        self.value: int = 0
        self.reset_at: float = 0.0


class _InMemoryStore:
    """
    Global in-memory store backed by defaultdict + threading.Lock.
    Stores {_key: _InMemoryCounter(value, reset_at)}.

    NOTE: This is a per-process fallback. It will NOT share state across
    multiple uvicorn/gunicorn workers. Use Redis in production multi-worker
    deployments to get distributed rate limiting.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Dict[str, _InMemoryCounter] = defaultdict(_InMemoryCounter)

    def incr(self, key: str, window_seconds: int) -> int:
        """
        Increment counter for `key` and return the new value.
        Resets the counter when the window has elapsed.
        """
        now = time.monotonic()
        with self._lock:
            counter = self._data[key]
            if now >= counter.reset_at:
                counter.value = 0
                counter.reset_at = now + window_seconds
            counter.value += 1
            return counter.value

    def ttl_remaining(self, key: str) -> int:
        """Return seconds until the current window expires (0 if key missing)."""
        now = time.monotonic()
        with self._lock:
            counter = self._data.get(key)
            if counter is None:
                return 0
            remaining = counter.reset_at - now
            return max(0, int(remaining))


# Process-global fallback store (singleton)
_inmemory_store = _InMemoryStore()


# ──────────────────────────────────────────────────────────────────────────────
# Redis-backed rate limiter
# ──────────────────────────────────────────────────────────────────────────────

class _RedisRateLimiter:
    """
    Redis-based sliding-window rate limiter.
    Uses INCR + EXPIRE (simplified fixed window) to track request counts.
    """

    def __init__(self) -> None:
        try:
            from app.cache.redis_cache import get_redis_cache
            self._cache = get_redis_cache()
        except Exception as exc:
            logger.warning(f"Redis unavailable for rate limiting, falling back to in-memory: {exc}")
            self._cache = None

    def _is_available(self) -> bool:
        if self._cache is None:
            return False
        try:
            self._cache.client.ping()
            return True
        except Exception:
            return False

    def incr(self, key: str, window_seconds: int) -> Tuple[int, bool]:
        """
        Increment the counter for `key` and return (new_value, is_redis).

        - If Redis is available: INCR + EXPIRE (set TTL only on first set).
        - If Redis is unavailable: falls back to in-memory store.
        """
        if self._is_available():
            try:
                new_val = self._cache.increment(key, 1)
                if new_val is None:
                    raise RuntimeError("Redis INCR returned None")

                # Set TTL only the first time the key is created (when value == 1)
                if new_val == 1:
                    self._cache.expire(key, window_seconds)

                return int(new_val), True
            except Exception as exc:
                logger.warning(f"Redis INCR/EXPIRE failed, using fallback: {exc}")

        # Fallback to in-memory
        return _inmemory_store.incr(key, window_seconds), False

    def ttl_remaining(self, key: str) -> int:
        """
        Return seconds until the current window expires.
        Tries Redis first, falls back to in-memory store.
        """
        if self._is_available():
            try:
                return max(0, self._cache.get_ttl(key))
            except Exception:
                pass
        return _inmemory_store.ttl_remaining(key)


# ──────────────────────────────────────────────────────────────────────────────
# Rate limit tiers (windows in seconds)
# ──────────────────────────────────────────────────────────────────────────────

RATE_LIMIT_TIERS = [
    ("per_minute", 5,   60),      # 5 requests / 60 seconds
    ("per_hour",   20,  3600),    # 20 requests / 3600 seconds (1 hour)
    ("per_day",    50,  86400),   # 50 requests / 86400 seconds (1 day)
]


# ──────────────────────────────────────────────────────────────────────────────
# RateLimitExceeded – structured exception raised when limit is breached
# ──────────────────────────────────────────────────────────────────────────────

class RateLimitExceeded(HTTPException):
    """
    HTTP 429 exception raised when any rate limit tier is exceeded.
    The `detail` dict carries the exact tier breached and retry-after seconds.
    """

    def __init__(self, retry_after: int, tier: str, limit: int) -> None:
        detail = {
            "error": "TOO_MANY_REQUESTS",
            "tier": tier,
            "limit": limit,
            "retry_after_seconds": retry_after,
            "message": f"Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau {retry_after} giây.",
        }
        super().__init__(status_code=429, detail=detail)
        self.tier = tier
        self.limit = limit
        self.retry_after = retry_after


# ──────────────────────────────────────────────────────────────────────────────
# Per-tier limit + window from env (with sensible defaults)
# ──────────────────────────────────────────────────────────────────────────────

def _get_tiers() -> List[Tuple[str, int, int]]:
    """
    Build the active rate-limit tiers from environment variables.
    Format: RATE_LIMIT_PER_MINUTE=5, RATE_LIMIT_PER_HOUR=20, RATE_LIMIT_PER_DAY=50
    Set to 0 to disable a specific tier.
    """
    tiers: List[Tuple[str, int, int]] = []
    env_map = {
        "per_minute": ("RATE_LIMIT_PER_MINUTE", 5, 60),
        "per_hour":   ("RATE_LIMIT_PER_HOUR",   20, 3600),
        "per_day":    ("RATE_LIMIT_PER_DAY",     50, 86400),
    }
    for tier_name, (env_var, default_limit, window) in env_map.items():
        import os
        raw = os.getenv(env_var)
        if raw is not None:
            try:
                limit = int(raw.strip())
            except ValueError:
                limit = default_limit
        else:
            limit = default_limit
        if limit > 0:
            tiers.append((tier_name, limit, window))
    return tiers


# ──────────────────────────────────────────────────────────────────────────────
# Decorator
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def rate_limit(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorator to enforce a per-user rate limit on an endpoint.

    Usage:
        @rate_limit(limit=5, window=60)
        async def my_endpoint(student: Student = Depends(get_current_student)):
            ...

    Args:
        limit:   Max requests allowed within `window` seconds.
                 If None, reads from env var RATE_LIMIT_PER_MINUTE (default 5).
        window:  Window size in seconds.
                 If None, reads from env var RATE_LIMIT_PER_MINUTE_WINDOW (default 60).
        key_func: Callable that receives the same kwargs as the decorated function
                  and returns a unique key string (e.g. "student:{student_id}").
                  If None, defaults to keying by `student_id` on the first arg
                  that has a `.id` attribute (works with SQLAlchemy Student model).

    The decorator checks ALL active tiers (minute / hour / day) and returns 429
    on the first one that is breached, with the exact retry-after seconds.

    Redis is used for tracking when available; falls back to a thread-safe
    in-memory dict if Redis is unreachable (e.g. connection error 10061).
    """

    # Resolve effective limit / window (None → env defaults)
    import os
    _limit = (
        limit
        if limit is not None
        else int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
    )
    _window = (
        window
        if window is not None
        else int(os.getenv("RATE_LIMIT_PER_MINUTE_WINDOW", "60"))
    )
    _tiers = _get_tiers()

    # Shared limiter instance (process-global, thread-safe)
    _limiter = _RedisRateLimiter()

    def _default_key_func(**kwargs) -> str:
        # Find first arg that looks like a Student model with .id
        for arg in kwargs.values():
            if hasattr(arg, "id") and isinstance(arg.id, int):
                return f"student:{arg.id}"
        # Fallback: use "user:unknown"
        return "user:unknown"

    _key_func = key_func or _default_key_func

    def decorator(fn: Callable) -> Callable:
        # FastAPI routes are always async coroutines; sync endpoints are rare
        # and not used in this project, so we assume async.
        is_async = asyncio.iscoroutinefunction(fn)

        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            key = _key_func(**kwargs)
            for tier_name, tier_limit, tier_window in _tiers:
                rl_key = f"rate_limit:{tier_name}:{key}"
                current_count, _ = _limiter.incr(rl_key, tier_window)
                if current_count > tier_limit:
                    retry_after = _limiter.ttl_remaining(rl_key)
                    if retry_after <= 0:
                        retry_after = tier_window
                    raise RateLimitExceeded(
                        retry_after=retry_after,
                        tier=tier_name,
                        limit=tier_limit,
                    )
            return await fn(*args, **kwargs)

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            key = _key_func(**kwargs)
            for tier_name, tier_limit, tier_window in _tiers:
                rl_key = f"rate_limit:{tier_name}:{key}"
                current_count, _ = _limiter.incr(rl_key, tier_window)
                if current_count > tier_limit:
                    retry_after = _limiter.ttl_remaining(rl_key)
                    if retry_after <= 0:
                        retry_after = tier_window
                    raise RateLimitExceeded(
                        retry_after=retry_after,
                        tier=tier_name,
                        limit=tier_limit,
                    )
            return fn(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper

    return decorator


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: simple per-minute limiter usable without a key_func
# (legacy signature kept for maximum compatibility with the task description)
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def simple_rate_limit(limit: int, window: int) -> Callable:
    """
    Legacy convenience decorator for a single limit+window tier.
    Uses `student_id` extracted from `kwargs["current_student"].id`.

    Example:
        @simple_rate_limit(limit=5, window=60)
        async def my_endpoint(message: ChatMessage,
                               current_student: Student = Depends(get_current_student)):
            ...
    """
    _limiter = _RedisRateLimiter()

    def decorator(fn: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(fn)

        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            # Try to find current_student in kwargs
            student = kwargs.get("current_student")
            if student is not None and hasattr(student, "id"):
                key = f"student:{student.id}"
            else:
                key = "user:unknown"

            rl_key = f"rate_limit:{key}"
            current_count, _ = _limiter.incr(rl_key, window)
            if current_count > limit:
                retry_after = _limiter.ttl_remaining(rl_key)
                if retry_after <= 0:
                    retry_after = window
                raise RateLimitExceeded(
                    retry_after=retry_after,
                    tier="per_minute",
                    limit=limit,
                )
            return await fn(*args, **kwargs)

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            student = kwargs.get("current_student")
            if student is not None and hasattr(student, "id"):
                key = f"student:{student.id}"
            else:
                key = "user:unknown"

            rl_key = f"rate_limit:{key}"
            current_count, _ = _limiter.incr(rl_key, window)
            if current_count > limit:
                retry_after = _limiter.ttl_remaining(rl_key)
                if retry_after <= 0:
                    retry_after = window
                raise RateLimitExceeded(
                    retry_after=retry_after,
                    tier="per_minute",
                    limit=limit,
                )
            return fn(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper

    return decorator
