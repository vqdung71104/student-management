"""
Message Queue Service
Service layer để tích hợp Redis Cache + RabbitMQ vào chatbot
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.cache.redis_cache import (
    get_redis_cache,
    cache_conversation_state,
    get_conversation_state,
    cache_class_preferences,
    get_class_preferences,
    clear_class_preferences
)
from app.queue.rabbitmq_manager import (
    publish_chat_message,
    publish_class_preference,
    publish_notification
)
import logging

logger = logging.getLogger(__name__)


class MessageQueueService:
    """Service for handling message queue operations"""
    
    @staticmethod
    async def handle_chat_message(
        student_id: int,
        message: str,
        response: str,
        intent: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Handle chat message: cache + queue
        
        Flow:
        1. Cache conversation state in Redis
        2. Publish message to RabbitMQ queue
        3. Worker will save to database
        
        Args:
            student_id: Student ID
            message: User message
            response: Bot response
            intent: Detected intent
            metadata: Additional metadata
        
        Returns:
            True if successful
        """
        try:
            # 1. Cache conversation state
            conversation_state = {
                'last_message': message,
                'last_response': response,
                'last_intent': intent,
                'last_updated': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            cache_success = cache_conversation_state(student_id, conversation_state)
            
            if not cache_success:
                logger.warning(f"Failed to cache conversation for student {student_id}")
            
            # 2. Publish to RabbitMQ
            queue_success = publish_chat_message(
                student_id=student_id,
                message=message,
                response=response,
                intent=intent,
                metadata=metadata
            )
            
            if not queue_success:
                logger.error(f"Failed to publish chat message for student {student_id}")
                return False
            
            logger.info(f"✅ Chat message handled for student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            return False
    
    @staticmethod
    async def update_class_preferences(
        student_id: int,
        preference_key: str,
        preference_value: Any,
        step: str = 'in_progress'
    ) -> Optional[Dict[str, Any]]:
        """
        Update class preferences incrementally
        
        Flow:
        1. Get current preferences from Redis
        2. Update with new preference
        3. Cache updated preferences
        4. Publish to queue (if step is 'complete')
        
        Args:
            student_id: Student ID
            preference_key: Preference key (e.g., 'time_period')
            preference_value: Preference value
            step: Current step ('in_progress' or 'complete')
        
        Returns:
            Updated preferences dict
        """
        try:
            # 1. Get current preferences
            preferences = get_class_preferences(student_id) or {}
            
            # 2. Update preferences
            preferences[preference_key] = preference_value
            preferences['last_updated'] = datetime.now().isoformat()
            preferences['step'] = step
            
            # 3. Cache updated preferences
            cache_success = cache_class_preferences(student_id, preferences)
            
            if not cache_success:
                logger.warning(f"Failed to cache preferences for student {student_id}")
            
            # 4. Publish to queue if complete
            if step == 'complete':
                queue_success = publish_class_preference(
                    student_id=student_id,
                    preferences=preferences,
                    step=step
                )
                
                if not queue_success:
                    logger.error(f"Failed to publish preferences for student {student_id}")
            
            logger.info(f"✅ Preferences updated for student {student_id}: {preference_key}={preference_value}")
            return preferences
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return None
    
    @staticmethod
    async def get_current_preferences(student_id: int) -> Optional[Dict[str, Any]]:
        """
        Get current class preferences from cache
        
        Args:
            student_id: Student ID
        
        Returns:
            Preferences dict or None
        """
        return get_class_preferences(student_id)
    
    @staticmethod
    async def clear_preferences(student_id: int) -> bool:
        """
        Clear class preferences cache
        
        Args:
            student_id: Student ID
        
        Returns:
            True if successful
        """
        return clear_class_preferences(student_id)
    
    @staticmethod
    async def send_notification(
        student_id: int,
        notification_type: str,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Send notification via queue
        
        Args:
            student_id: Student ID
            notification_type: Type of notification
            title: Notification title
            content: Notification content
            metadata: Additional metadata
        
        Returns:
            True if successful
        """
        try:
            success = publish_notification(
                student_id=student_id,
                notification_type=notification_type,
                title=title,
                content=content,
                metadata=metadata
            )
            
            if success:
                logger.info(f"✅ Notification sent for student {student_id}: {title}")
            else:
                logger.error(f"Failed to send notification for student {student_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    @staticmethod
    async def get_conversation_history(student_id: int) -> Optional[Dict[str, Any]]:
        """
        Get conversation history from cache
        
        Args:
            student_id: Student ID
        
        Returns:
            Conversation state dict or None
        """
        return get_conversation_state(student_id)
