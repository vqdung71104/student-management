"""
Test RabbitMQ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
import time
from app.queue.rabbitmq_manager import (
    RabbitMQManager,
    get_rabbitmq_manager,
    publish_chat_message,
    publish_class_preference,
    publish_notification
)


@pytest.fixture
def rabbitmq():
    """RabbitMQ fixture"""
    mq = RabbitMQManager()
    yield mq
    # Cleanup
    mq.close()


def test_rabbitmq_connection(rabbitmq):
    """Test RabbitMQ connection"""
    assert rabbitmq.connection is not None
    assert not rabbitmq.connection.is_closed
    print("✅ RabbitMQ connection successful")


def test_queue_declaration(rabbitmq):
    """Test queue declaration"""
    queues = [
        RabbitMQManager.QUEUE_CHAT_MESSAGES,
        RabbitMQManager.QUEUE_CLASS_PREFERENCES,
        RabbitMQManager.QUEUE_NOTIFICATION
    ]
    
    for queue in queues:
        size = rabbitmq.get_queue_size(queue)
        assert size >= 0
        print(f"✅ Queue '{queue}' exists with {size} messages")


def test_publish_message(rabbitmq):
    """Test publishing message"""
    message = {
        'type': 'test',
        'content': 'Hello, RabbitMQ!',
        'test_id': 123
    }
    
    # Publish
    success = rabbitmq.publish_message(
        queue_name=RabbitMQManager.QUEUE_CHAT_MESSAGES,
        message=message
    )
    
    assert success
    
    # Check queue size
    size = rabbitmq.get_queue_size(RabbitMQManager.QUEUE_CHAT_MESSAGES)
    assert size > 0
    print(f"✅ Message published. Queue size: {size}")


def test_publish_chat_message():
    """Test publishing chat message"""
    success = publish_chat_message(
        student_id=1,
        message="Tôi muốn đăng ký lớp",
        response="Bạn muốn học buổi nào?",
        intent="class_registration_suggestion",
        metadata={'step': 1}
    )
    
    assert success
    print("✅ Chat message published")


def test_publish_class_preference():
    """Test publishing class preference"""
    preferences = {
        'time_period': 'morning',
        'avoid_early_start': True,
        'avoid_days': ['Saturday']
    }
    
    success = publish_class_preference(
        student_id=1,
        preferences=preferences,
        step='complete'
    )
    
    assert success
    print("✅ Class preference published")


def test_publish_notification():
    """Test publishing notification"""
    success = publish_notification(
        student_id=1,
        notification_type='class_registration',
        title='Lớp đã đầy',
        content='Lớp IT3170-001 đã đầy. Vui lòng chọn lớp khác.',
        metadata={'class_id': 'IT3170-001'}
    )
    
    assert success
    print("✅ Notification published")


def test_consumer(rabbitmq):
    """Test consumer (manual test)"""
    print("\n⚠️ Consumer test requires manual verification")
    print("1. Run worker: python app/queue/workers/message_worker.py --type all")
    print("2. Publish messages using above tests")
    print("3. Check worker logs")
    print("4. Check database tables")


def test_purge_queue(rabbitmq):
    """Test purge queue"""
    # Publish some test messages
    for i in range(5):
        rabbitmq.publish_message(
            queue_name=RabbitMQManager.QUEUE_CHAT_MESSAGES,
            message={'test': i}
        )
    
    # Check size
    size_before = rabbitmq.get_queue_size(RabbitMQManager.QUEUE_CHAT_MESSAGES)
    print(f"Queue size before purge: {size_before}")
    
    # Purge
    success = rabbitmq.purge_queue(RabbitMQManager.QUEUE_CHAT_MESSAGES)
    assert success
    
    # Check size again
    size_after = rabbitmq.get_queue_size(RabbitMQManager.QUEUE_CHAT_MESSAGES)
    assert size_after == 0
    print(f"✅ Queue purged. Size after: {size_after}")


def test_message_with_routing_key(rabbitmq):
    """Test message with custom routing key"""
    message = {
        'type': 'chat_message',
        'student_id': 1,
        'content': 'Test routing'
    }
    
    success = rabbitmq.publish_message(
        queue_name=RabbitMQManager.QUEUE_CHAT_MESSAGES,
        message=message,
        exchange=RabbitMQManager.EXCHANGE_CHAT,
        routing_key='chat.message.test'
    )
    
    assert success
    print("✅ Message with routing key published")


if __name__ == "__main__":
    print("🧪 Running RabbitMQ Tests...\n")
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
