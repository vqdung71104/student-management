"""
Redis Cache Manager
Quản lý cache cho chatbot preferences và conversation state
"""

import redis
import json
import time
import fnmatch
from typing import Optional, Dict, Any, List
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class RedisCache:
    """Redis Cache Manager for chatbot data"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis connection
        
        Args:
            host: Redis host (default from env)
            port: Redis port (default from env)
            db: Redis database number
            password: Redis password (default from env)
            decode_responses: Auto decode bytes to string
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.password = password or os.getenv('REDIS_PASSWORD', None)
        self.db = db
        
        # Create Redis connection
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
            socket_keepalive=True,
        )

        # Test connection — gracefully fall back to None on Error 10061 / ConnectionError
        try:
            self.client.ping()
            print(f"[RedisCache] connected: {self.host}:{self.port}")
        except redis.ConnectionError as e:
            print(f"[RedisCache] ConnectionError {e} — running without Redis (in-memory fallback)")
            self.client = None
        except Exception as e:
            print(f"[RedisCache] Redis init error {e} — running without Redis")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                # Try to parse JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Error getting key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            ttl: Time to live in seconds (optional)
        
        Returns:
            True if successful
        """
        try:
            # Serialize to JSON if dict or list
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            print(f"Error setting key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted
        """
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Error checking key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for key
        
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Error getting TTL for {key}: {e}")
            return -2
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiry time for key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            print(f"Error setting expiry for {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment integer value
        
        Args:
            key: Cache key
            amount: Increment amount
        
        Returns:
            New value or None if error
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            print(f"Error incrementing {key}: {e}")
            return None
    
    def get_keys(self, pattern: str) -> list:
        """
        Get all keys matching pattern
        
        Args:
            pattern: Pattern (e.g., "user:*")
        
        Returns:
            List of matching keys
        """
        try:
            return self.client.keys(pattern)
        except Exception as e:
            print(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    def flush_db(self) -> bool:
        """
        Clear all keys in current database
        
        ⚠️ Use with caution!
        
        Returns:
            True if successful
        """
        try:
            return self.client.flushdb()
        except Exception as e:
            print(f"Error flushing database: {e}")
            return False
    
    def close(self):
        """Close Redis connection"""
        try:
            self.client.close()
            print("✅ Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis connection: {e}")


# Singleton instance
_redis_cache_instance: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """
    Get Redis cache singleton instance.

    Returns:
        RedisCache instance (Redis-backed or in-memory fallback).
        Never raises — always returns a usable instance.
    """
    global _redis_cache_instance

    if _redis_cache_instance is None:
        try:
            _redis_cache_instance = RedisCache()
        except Exception as e:
            # Last-resort fallback — creates a dummy instance with client=None
            print(f"[RedisCache] Singleton init failed: {e} — using in-memory fallback")
            _redis_cache_instance = _InMemoryRedisCacheFallback()

    return _redis_cache_instance


class _InMemoryRedisCacheFallback:
    """Ultra-light in-memory fallback used when Redis is unavailable at startup."""

    def __init__(self):
        self.store = {}

    def get(self, key: str) -> Optional[Any]:
        item = self.store.get(key)
        if item is None:
            return None
        value, expires = item
        if expires < time.time():
            del self.store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        import json
        serialized = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        expires = (time.time() + ttl) if ttl else (time.time() + 3600)
        self.store[key] = (serialized, expires)
        return True

    def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        item = self.store.get(key)
        if item and item[1] >= time.time():
            return True
        return False

    def ttl(self, key: str) -> int:
        item = self.store.get(key)
        if not item:
            return -2
        remaining = item[1] - time.time()
        return max(-2, int(remaining))

    def expire(self, key: str, ttl: int) -> bool:
        if key in self.store:
            value, _ = self.store[key]
            self.store[key] = (value, time.time() + ttl)
            return True
        return False

    def incrby(self, key: str, amount: int = 1) -> Optional[int]:
        item = self.store.get(key)
        if item is None:
            self.store[key] = (str(amount), time.time() + 3600)
            return amount
        current = int(item[0])
        new_val = current + amount
        self.store[key] = (str(new_val), item[1])
        return new_val

    def keys(self, pattern: str) -> list:
        import fnmatch
        return [k for k in self.store if fnmatch.fnmatch(k, pattern)]

    def flushdb(self) -> bool:
        self.store.clear()
        return True

    def close(self) -> None:
        pass


# Convenience functions for common cache operations

def cache_conversation_state(
    student_id: int,
    state: Dict[str, Any],
    ttl: int = 3600
) -> bool:
    """
    Cache conversation state for a student
    
    Args:
        student_id: Student ID
        state: Conversation state dict
        ttl: Time to live (default 1 hour)
    
    Returns:
        True if successful
    """
    cache = get_redis_cache()
    key = f"conversation:{student_id}"
    return cache.set(key, state, ttl)


def get_conversation_state(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Get conversation state for a student
    
    Args:
        student_id: Student ID
    
    Returns:
        Conversation state dict or None
    """
    cache = get_redis_cache()
    key = f"conversation:{student_id}"
    return cache.get(key)


def cache_class_preferences(
    student_id: int,
    preferences: Dict[str, Any],
    ttl: int = 3600
) -> bool:
    """
    Cache class registration preferences
    
    Args:
        student_id: Student ID
        preferences: Preferences dict
        ttl: Time to live (default 1 hour)
    
    Returns:
        True if successful
    """
    cache = get_redis_cache()
    key = f"class_preferences:{student_id}"
    return cache.set(key, preferences, ttl)


def get_class_preferences(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Get class registration preferences
    
    Args:
        student_id: Student ID
    
    Returns:
        Preferences dict or None
    """
    cache = get_redis_cache()
    key = f"class_preferences:{student_id}"
    return cache.get(key)


def clear_class_preferences(student_id: int) -> bool:
    """
    Clear class registration preferences
    
    Args:
        student_id: Student ID
    
    Returns:
        True if deleted
    """
    cache = get_redis_cache()
    key = f"class_preferences:{student_id}"
    return cache.delete(key)
