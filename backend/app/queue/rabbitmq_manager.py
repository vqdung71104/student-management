"""
RabbitMQ Message Queue Manager
Quản lý message queue cho async processing
"""

import pika
import json
import os
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQManager:
    """RabbitMQ Connection and Queue Manager"""
    
    # Queue names
    QUEUE_CHAT_MESSAGES = "chat_messages"
    QUEUE_CLASS_PREFERENCES = "class_preferences"
    QUEUE_NOTIFICATION = "notifications"
    
    # Exchange names
    EXCHANGE_CHAT = "chat_exchange"
    EXCHANGE_SYSTEM = "system_exchange"
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        virtual_host: str = '/'
    ):
        """
        Initialize RabbitMQ connection
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: Username
            password: Password
            virtual_host: Virtual host
        """
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port or int(os.getenv('RABBITMQ_PORT', 5672))
        self.username = username or os.getenv('RABBITMQ_USER', 'guest')
        self.password = password or os.getenv('RABBITMQ_PASS', 'guest')
        self.virtual_host = virtual_host
        
        # Connection and channel
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        
        # Connect
        self._connect()
        
        # Setup exchanges and queues
        self._setup_queues()
    
    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info(f"✅ RabbitMQ connected: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ RabbitMQ connection failed: {e}")
            raise
    
    def _setup_queues(self):
        """Setup exchanges and queues"""
        try:
            # Declare exchanges
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_CHAT,
                exchange_type='topic',
                durable=True
            )
            
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_SYSTEM,
                exchange_type='direct',
                durable=True
            )
            
            # Declare queues
            # Chat messages queue
            self.channel.queue_declare(
                queue=self.QUEUE_CHAT_MESSAGES,
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,  # 24 hours
                    'x-max-length': 10000  # Max 10k messages
                }
            )
            
            # Class preferences queue
            self.channel.queue_declare(
                queue=self.QUEUE_CLASS_PREFERENCES,
                durable=True,
                arguments={
                    'x-message-ttl': 3600000,  # 1 hour
                    'x-max-length': 5000
                }
            )
            
            # Notification queue
            self.channel.queue_declare(
                queue=self.QUEUE_NOTIFICATION,
                durable=True,
                arguments={
                    'x-message-ttl': 604800000,  # 7 days
                    'x-max-length': 50000
                }
            )
            
            # Bind queues to exchanges
            self.channel.queue_bind(
                exchange=self.EXCHANGE_CHAT,
                queue=self.QUEUE_CHAT_MESSAGES,
                routing_key='chat.message.*'
            )
            
            self.channel.queue_bind(
                exchange=self.EXCHANGE_CHAT,
                queue=self.QUEUE_CLASS_PREFERENCES,
                routing_key='chat.preferences.*'
            )
            
            self.channel.queue_bind(
                exchange=self.EXCHANGE_SYSTEM,
                queue=self.QUEUE_NOTIFICATION,
                routing_key='notification'
            )
            
            logger.info("✅ RabbitMQ queues and exchanges setup complete")
        except Exception as e:
            logger.error(f"Error setting up queues: {e}")
            raise
    
    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        routing_key: str = None,
        exchange: str = None
    ) -> bool:
        """
        Publish message to queue
        
        Args:
            queue_name: Queue name
            message: Message dict
            routing_key: Routing key (optional)
            exchange: Exchange name (optional, defaults to queue)
        
        Returns:
            True if successful
        """
        try:
            # Add timestamp
            message['timestamp'] = datetime.now().isoformat()
            
            # Serialize to JSON
            body = json.dumps(message, ensure_ascii=False)
            
            # Determine exchange and routing key
            if exchange is None:
                exchange = ''  # Default exchange
            
            if routing_key is None:
                routing_key = queue_name
            
            # Publish
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                    timestamp=int(datetime.now().timestamp())
                )
            )
            
            logger.info(f"📤 Published to {queue_name}: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def consume_messages(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False
    ):
        """
        Consume messages from queue
        
        Args:
            queue_name: Queue name
            callback: Callback function(channel, method, properties, body)
            auto_ack: Auto acknowledge messages
        """
        try:
            logger.info(f"👂 Listening to queue: {queue_name}")
            
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=auto_ack
            )
            
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping consumer...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise
    
    def get_queue_size(self, queue_name: str) -> int:
        """
        Get number of messages in queue
        
        Args:
            queue_name: Queue name
        
        Returns:
            Number of messages
        """
        try:
            method = self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                passive=True  # Don't create if doesn't exist
            )
            return method.method.message_count
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0
    
    def purge_queue(self, queue_name: str) -> bool:
        """
        Clear all messages from queue
        
        ⚠️ Use with caution!
        
        Args:
            queue_name: Queue name
        
        Returns:
            True if successful
        """
        try:
            self.channel.queue_purge(queue=queue_name)
            logger.info(f"🗑️ Purged queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error purging queue: {e}")
            return False
    
    def close(self):
        """Close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("✅ RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager enter"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Singleton instance
_rabbitmq_instance: Optional[RabbitMQManager] = None


def get_rabbitmq_manager() -> RabbitMQManager:
    """
    Get RabbitMQ manager singleton instance
    
    Returns:
        RabbitMQManager instance
    """
    global _rabbitmq_instance
    
    if _rabbitmq_instance is None:
        _rabbitmq_instance = RabbitMQManager()
    
    return _rabbitmq_instance


# Convenience functions for publishing messages

def publish_chat_message(
    student_id: int,
    message: str,
    response: str,
    intent: str,
    metadata: Dict[str, Any] = None
) -> bool:
    """
    Publish chat message to queue
    
    Args:
        student_id: Student ID
        message: User message
        response: Bot response
        intent: Detected intent
        metadata: Additional metadata
    
    Returns:
        True if successful
    """
    mq = get_rabbitmq_manager()
    
    payload = {
        'type': 'chat_message',
        'student_id': student_id,
        'message': message,
        'response': response,
        'intent': intent,
        'metadata': metadata or {}
    }
    
    return mq.publish_message(
        queue_name=RabbitMQManager.QUEUE_CHAT_MESSAGES,
        message=payload,
        exchange=RabbitMQManager.EXCHANGE_CHAT,
        routing_key='chat.message.new'
    )


def publish_class_preference(
    student_id: int,
    preferences: Dict[str, Any],
    step: str = 'complete'
) -> bool:
    """
    Publish class preference to queue
    
    Args:
        student_id: Student ID
        preferences: Preference dict
        step: Current step in preference collection
    
    Returns:
        True if successful
    """
    mq = get_rabbitmq_manager()
    
    payload = {
        'type': 'class_preference',
        'student_id': student_id,
        'preferences': preferences,
        'step': step
    }
    
    return mq.publish_message(
        queue_name=RabbitMQManager.QUEUE_CLASS_PREFERENCES,
        message=payload,
        exchange=RabbitMQManager.EXCHANGE_CHAT,
        routing_key='chat.preferences.update'
    )


def publish_notification(
    student_id: int,
    notification_type: str,
    title: str,
    content: str,
    metadata: Dict[str, Any] = None
) -> bool:
    """
    Publish notification to queue
    
    Args:
        student_id: Student ID
        notification_type: Type of notification
        title: Notification title
        content: Notification content
        metadata: Additional metadata
    
    Returns:
        True if successful
    """
    mq = get_rabbitmq_manager()
    
    payload = {
        'type': 'notification',
        'student_id': student_id,
        'notification_type': notification_type,
        'title': title,
        'content': content,
        'metadata': metadata or {}
    }
    
    return mq.publish_message(
        queue_name=RabbitMQManager.QUEUE_NOTIFICATION,
        message=payload,
        exchange=RabbitMQManager.EXCHANGE_SYSTEM,
        routing_key='notification'
    )
