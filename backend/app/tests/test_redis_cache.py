"""
Test Redis Cache
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
from app.cache.redis_cache import (
    RedisCache,
    cache_conversation_state,
    get_conversation_state,
    cache_class_preferences,
    get_class_preferences,
    clear_class_preferences
)


@pytest.fixture
def redis_cache():
    """Redis cache fixture"""
    cache = RedisCache()
    yield cache
    # Cleanup
    cache.flush_db()
    cache.close()


def test_redis_connection(redis_cache):
    """Test Redis connection"""
    assert redis_cache.client.ping()
    print("✅ Redis connection successful")


def test_set_get_string(redis_cache):
    """Test set and get string value"""
    key = "test:string"
    value = "Hello, Redis!"
    
    # Set
    assert redis_cache.set(key, value)
    
    # Get
    result = redis_cache.get(key)
    assert result == value
    print(f"✅ String set/get: {result}")


def test_set_get_dict(redis_cache):
    """Test set and get dict value"""
    key = "test:dict"
    value = {
        'name': 'John',
        'age': 25,
        'courses': ['IT3170', 'IT3080']
    }
    
    # Set
    assert redis_cache.set(key, value)
    
    # Get
    result = redis_cache.get(key)
    assert result == value
    assert result['name'] == 'John'
    print(f"✅ Dict set/get: {result}")


def test_ttl(redis_cache):
    """Test TTL (Time To Live)"""
    key = "test:ttl"
    value = "Temporary value"
    ttl = 10  # 10 seconds
    
    # Set with TTL
    assert redis_cache.set(key, value, ttl)
    
    # Check TTL
    remaining_ttl = redis_cache.get_ttl(key)
    assert 0 < remaining_ttl <= ttl
    print(f"✅ TTL test: {remaining_ttl} seconds remaining")


def test_exists_delete(redis_cache):
    """Test exists and delete"""
    key = "test:delete"
    value = "To be deleted"
    
    # Set
    redis_cache.set(key, value)
    
    # Check exists
    assert redis_cache.exists(key)
    
    # Delete
    assert redis_cache.delete(key)
    
    # Check not exists
    assert not redis_cache.exists(key)
    print("✅ Exists and delete test passed")


def test_conversation_state():
    """Test conversation state caching"""
    student_id = 1
    state = {
        'last_message': 'Tôi muốn đăng ký lớp',
        'last_response': 'Bạn muốn học buổi nào?',
        'last_intent': 'class_registration_suggestion',
        'step': 1
    }
    
    # Cache
    assert cache_conversation_state(student_id, state, ttl=3600)
    
    # Get
    result = get_conversation_state(student_id)
    assert result is not None
    assert result['last_intent'] == 'class_registration_suggestion'
    print(f"✅ Conversation state: {result}")


def test_class_preferences():
    """Test class preferences caching"""
    student_id = 1
    preferences = {
        'time_period': 'morning',
        'avoid_early_start': True,
        'avoid_late_end': False,
        'avoid_days': ['Saturday', 'Sunday']
    }
    
    # Cache
    assert cache_class_preferences(student_id, preferences, ttl=3600)
    
    # Get
    result = get_class_preferences(student_id)
    assert result is not None
    assert result['time_period'] == 'morning'
    assert len(result['avoid_days']) == 2
    print(f"✅ Class preferences: {result}")
    
    # Clear
    assert clear_class_preferences(student_id)
    
    # Check cleared
    result = get_class_preferences(student_id)
    assert result is None
    print("✅ Preferences cleared")


def test_increment(redis_cache):
    """Test increment counter"""
    key = "test:counter"
    
    # Increment
    count1 = redis_cache.increment(key, 1)
    assert count1 == 1
    
    count2 = redis_cache.increment(key, 5)
    assert count2 == 6
    
    print(f"✅ Increment test: {count2}")


def test_get_keys(redis_cache):
    """Test get keys by pattern"""
    # Set multiple keys
    redis_cache.set("user:1:name", "Alice")
    redis_cache.set("user:2:name", "Bob")
    redis_cache.set("user:3:name", "Charlie")
    redis_cache.set("product:1:name", "Book")
    
    # Get user keys
    user_keys = redis_cache.get_keys("user:*")
    assert len(user_keys) >= 3
    print(f"✅ Found {len(user_keys)} user keys")


if __name__ == "__main__":
    print("🧪 Running Redis Cache Tests...\n")
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
