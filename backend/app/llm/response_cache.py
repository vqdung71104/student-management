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
    def __init__(self, redis_url: Optional[str] = None):
        self.client = None
        if _REDIS_AVAILABLE and redis_url:
            try:
                self.client = redis.from_url(redis_url)
            except Exception:
                self.client = None
        if not self.client:
            self.client = InMemoryCache()

    def get(self, key: str) -> Optional[str]:
        if hasattr(self.client, 'get') and not isinstance(self.client, InMemoryCache):
            val = self.client.get(key)
            if val is None:
                return None
            return val.decode() if isinstance(val, bytes) else val
        return self.client.get(key)

    def set(self, key: str, value: str, ttl: int = CACHE_TTL):
        if hasattr(self.client, 'set') and not isinstance(self.client, InMemoryCache):
            self.client.set(key, value, ex=ttl)
        else:
            self.client.set(key, value, ttl)
