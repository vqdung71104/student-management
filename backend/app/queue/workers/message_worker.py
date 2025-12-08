"""
Chat Message Worker
Worker để xử lý chat messages từ RabbitMQ và lưu vào database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.queue.rabbitmq_manager import get_rabbitmq_manager, RabbitMQManager
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()


class ChatMessageLog(Base):
    """Chat message log table"""
    __tablename__ = "chat_message_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    intent = Column(String(255), nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class ClassPreferenceLog(Base):
    """Class preference log table"""
    __tablename__ = "class_preference_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    preferences = Column(JSON, nullable=False)
    step = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class NotificationLog(Base):
    """Notification log table"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


# Create database engine and session
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def process_chat_message(ch, method, properties, body):
    """
    Process chat message from queue
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        # Parse message
        message = json.loads(body)
        logger.info(f"📥 Processing chat message for student {message.get('student_id')}")
        
        # Save to database
        db = SessionLocal()
        try:
            log = ChatMessageLog(
                student_id=message['student_id'],
                message=message['message'],
                response=message['response'],
                intent=message['intent'],
                metadata=message.get('metadata', {}),
                timestamp=datetime.fromisoformat(message['timestamp'])
            )
            db.add(log)
            db.commit()
            
            logger.info(f"✅ Chat message saved to database (ID: {log.id})")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
            # Negative acknowledge - requeue message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def process_class_preference(ch, method, properties, body):
    """
    Process class preference from queue
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        # Parse message
        message = json.loads(body)
        logger.info(f"📥 Processing class preference for student {message.get('student_id')}")
        
        # Save to database
        db = SessionLocal()
        try:
            log = ClassPreferenceLog(
                student_id=message['student_id'],
                preferences=message['preferences'],
                step=message.get('step', 'complete'),
                timestamp=datetime.fromisoformat(message['timestamp'])
            )
            db.add(log)
            db.commit()
            
            logger.info(f"✅ Class preference saved to database (ID: {log.id})")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def process_notification(ch, method, properties, body):
    """
    Process notification from queue
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        # Parse message
        message = json.loads(body)
        logger.info(f"📥 Processing notification for student {message.get('student_id')}")
        
        # Save to database
        db = SessionLocal()
        try:
            log = NotificationLog(
                student_id=message['student_id'],
                notification_type=message['notification_type'],
                title=message['title'],
                content=message['content'],
                metadata=message.get('metadata', {}),
                timestamp=datetime.fromisoformat(message['timestamp'])
            )
            db.add(log)
            db.commit()
            
            logger.info(f"✅ Notification saved to database (ID: {log.id})")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker(worker_type: str = 'all'):
    """
    Start worker to process messages
    
    Args:
        worker_type: Type of worker ('chat', 'preference', 'notification', 'all')
    """
    logger.info(f"🚀 Starting worker: {worker_type}")
    
    mq = get_rabbitmq_manager()
    
    try:
        if worker_type in ['chat', 'all']:
            logger.info("👂 Starting chat message worker...")
            mq.channel.basic_consume(
                queue=RabbitMQManager.QUEUE_CHAT_MESSAGES,
                on_message_callback=process_chat_message,
                auto_ack=False
            )
        
        if worker_type in ['preference', 'all']:
            logger.info("👂 Starting class preference worker...")
            mq.channel.basic_consume(
                queue=RabbitMQManager.QUEUE_CLASS_PREFERENCES,
                on_message_callback=process_class_preference,
                auto_ack=False
            )
        
        if worker_type in ['notification', 'all']:
            logger.info("👂 Starting notification worker...")
            mq.channel.basic_consume(
                queue=RabbitMQManager.QUEUE_NOTIFICATION,
                on_message_callback=process_notification,
                auto_ack=False
            )
        
        logger.info("✅ Worker started successfully. Waiting for messages...")
        mq.channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
        mq.channel.stop_consuming()
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
    finally:
        mq.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Message Queue Worker')
    parser.add_argument(
        '--type',
        choices=['chat', 'preference', 'notification', 'all'],
        default='all',
        help='Type of worker to start'
    )
    
    args = parser.parse_args()
    start_worker(args.type)
