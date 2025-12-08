"""
Cache Module
Redis cache management
"""

from app.cache.redis_cache import (
    RedisCache,
    get_redis_cache,
    cache_conversation_state,
    get_conversation_state,
    cache_class_preferences,
    get_class_preferences,
    clear_class_preferences
)

__all__ = [
    'RedisCache',
    'get_redis_cache',
    'cache_conversation_state',
    'get_conversation_state',
    'cache_class_preferences',
    'get_class_preferences',
    'clear_class_preferences'
]
