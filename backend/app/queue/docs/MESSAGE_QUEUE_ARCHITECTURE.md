# MESSAGE QUEUE SYSTEM - ARCHITECTURE DOCUMENTATION

## 📚 Tổng quan

Hệ thống **Message Queue** sử dụng kiến trúc **async processing** với:

- **Redis Cache**: Lưu trữ tạm thời conversation state và preferences
- **RabbitMQ**: Message broker để xử lý bất đồng bộ
- **Worker**: Background process để lưu data vào database

---

## 🏗️ Kiến trúc tổng thể

```
┌──────────────┐
│   Frontend   │
│   (React)    │
└──────┬───────┘
       │
       ▼ HTTP Request
┌──────────────────────────────────────┐
│         FastAPI Backend              │
│  ┌────────────────────────────────┐  │
│  │  ChatBot Service               │  │
│  │  - Process message             │  │
│  │  - Detect intent               │  │
│  │  - Generate response           │  │
│  └────────┬───────────────────────┘  │
│           │                           │
│           ▼                           │
│  ┌────────────────────────────────┐  │
│  │  MessageQueueService           │  │
│  │  - Cache to Redis              │  │
│  │  - Publish to RabbitMQ         │  │
│  └────────┬───────────────────────┘  │
└───────────┼───────────────────────────┘
            │
            ├─────────────────┬──────────────────┐
            ▼                 ▼                  ▼
    ┌───────────────┐ ┌──────────────┐  ┌──────────────┐
    │  Redis Cache  │ │  RabbitMQ    │  │   Database   │
    │               │ │              │  │              │
    │ • Conv State  │ │ • Messages   │  │ • Permanent  │
    │ • Preferences │ │ • Queues     │  │   Storage    │
    │ • TTL: 1h     │ │ • TTL: 24h   │  │              │
    └───────────────┘ └──────┬───────┘  └──────▲───────┘
                             │                 │
                             ▼                 │
                     ┌──────────────┐          │
                     │    Worker    │──────────┘
                     │              │
                     │ • Consume    │
                     │ • Process    │
                     │ • Save DB    │
                     └──────────────┘
```

---

## 🔄 Workflow chi tiết

### 1. Chat Message Flow

```
User sends message
    ↓
FastAPI receives request
    ↓
ChatBot Service processes
    ↓
MessageQueueService.handle_chat_message()
    ↓
┌─────────────────┬─────────────────┐
▼                 ▼                 ▼
Redis Cache       RabbitMQ          Response to User
conversation      chat_messages     (Immediate)
state (TTL: 1h)   queue
                  ↓
                  Worker consumes
                  ↓
                  Save to chat_message_logs table
                  (Async, background)
```

**Code Example:**

```python
# In chatbot service
await MessageQueueService.handle_chat_message(
    student_id=1,
    message="Tôi muốn đăng ký lớp",
    response="Bạn muốn học buổi nào?",
    intent="class_registration_suggestion",
    metadata={"step": 1}
)
```

### 2. Class Preference Flow

```
User answers preference question
    ↓
Update preference in Redis
    ↓
MessageQueueService.update_class_preferences()
    ↓
┌─────────────────┬─────────────────┐
▼                 ▼                 ▼
Update Redis      If step==complete Ask next question
preferences       → Publish to      or show results
                  RabbitMQ
                  ↓
                  Worker consumes
                  ↓
                  Save to class_preference_logs table
```

**Code Example:**

```python
# Step 1: Time period
preferences = await MessageQueueService.update_class_preferences(
    student_id=1,
    preference_key='time_period',
    preference_value='morning',
    step='in_progress'
)

# Step 2: Avoid early
preferences = await MessageQueueService.update_class_preferences(
    student_id=1,
    preference_key='avoid_early_start',
    preference_value=True,
    step='in_progress'
)

# Step 3: Complete
preferences = await MessageQueueService.update_class_preferences(
    student_id=1,
    preference_key='avoid_days',
    preference_value=['Saturday'],
    step='complete'  # This will publish to RabbitMQ
)
```

---

## 📦 Components

### 1. Redis Cache (`app/cache/redis_cache.py`)

**Purpose:** Lưu trữ tạm thời data với TTL

**Key Features:**
- Connection pooling
- JSON serialization
- TTL support
- Singleton pattern

**Cache Keys:**

```
conversation:{student_id}          # Conversation state
class_preferences:{student_id}     # Class registration preferences
```

**Methods:**

```python
RedisCache:
  - get(key) -> Any
  - set(key, value, ttl) -> bool
  - delete(key) -> bool
  - exists(key) -> bool
  - get_ttl(key) -> int
  - expire(key, ttl) -> bool
```

**Configuration:**

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password  # Optional
```

### 2. RabbitMQ Manager (`app/queue/rabbitmq_manager.py`)

**Purpose:** Message broker cho async processing

**Queues:**

```python
QUEUE_CHAT_MESSAGES       # Chat messages
  - TTL: 24 hours
  - Max length: 10,000 messages

QUEUE_CLASS_PREFERENCES   # Class preferences
  - TTL: 1 hour
  - Max length: 5,000 messages

QUEUE_NOTIFICATION        # Notifications
  - TTL: 7 days
  - Max length: 50,000 messages
```

**Exchanges:**

```python
EXCHANGE_CHAT             # Topic exchange for chat
  - Routing keys: chat.message.*, chat.preferences.*

EXCHANGE_SYSTEM           # Direct exchange for system
  - Routing keys: notification
```

**Methods:**

```python
RabbitMQManager:
  - publish_message(queue, message, routing_key) -> bool
  - consume_messages(queue, callback) -> None
  - get_queue_size(queue) -> int
  - purge_queue(queue) -> bool
```

**Configuration:**

```env
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

### 3. Worker (`app/queue/workers/message_worker.py`)

**Purpose:** Background process để consume messages và lưu vào DB

**Worker Types:**

1. **Chat Message Worker**
   - Consumes from `chat_messages` queue
   - Saves to `chat_message_logs` table
   
2. **Class Preference Worker**
   - Consumes from `class_preferences` queue
   - Saves to `class_preference_logs` table

3. **Notification Worker**
   - Consumes from `notifications` queue
   - Saves to `notification_logs` table

**Database Tables:**

```sql
-- Chat message logs
CREATE TABLE chat_message_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    intent VARCHAR(255) NOT NULL,
    metadata JSON,
    timestamp DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX (student_id),
    INDEX (intent)
);

-- Class preference logs
CREATE TABLE class_preference_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    preferences JSON NOT NULL,
    step VARCHAR(100) NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX (student_id)
);

-- Notification logs
CREATE TABLE notification_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    timestamp DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX (student_id),
    INDEX (notification_type)
);
```

**Running Worker:**

```bash
# Run all workers
python app/queue/workers/message_worker.py --type all

# Run specific worker
python app/queue/workers/message_worker.py --type chat
python app/queue/workers/message_worker.py --type preference
python app/queue/workers/message_worker.py --type notification
```

### 4. Message Queue Service (`app/queue/message_queue_service.py`)

**Purpose:** Service layer để tích hợp vào chatbot

**Methods:**

```python
MessageQueueService:
  # Chat message handling
  - handle_chat_message(student_id, message, response, intent, metadata) -> bool
  
  # Preference management
  - update_class_preferences(student_id, key, value, step) -> Dict
  - get_current_preferences(student_id) -> Dict
  - clear_preferences(student_id) -> bool
  
  # Notification
  - send_notification(student_id, type, title, content, metadata) -> bool
  
  # History
  - get_conversation_history(student_id) -> Dict
```

---

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
# Update requirements.txt
pip install redis pika

# Or add to requirements.txt
echo "redis>=5.0.0" >> requirements.txt
echo "pika>=1.3.0" >> requirements.txt

# Install
pip install -r requirements.txt
```

### 2. Install & Start Redis

**Windows (using Chocolatey):**

```powershell
choco install redis-64
redis-server
```

**Ubuntu:**

```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Docker:**

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

### 3. Install & Start RabbitMQ

**Windows (using Chocolatey):**

```powershell
choco install rabbitmq
rabbitmq-service start
```

**Ubuntu:**

```bash
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
```

**Docker:**

```bash
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

**RabbitMQ Management UI:** http://localhost:15672 (guest/guest)

### 4. Configure Environment Variables

Create `.env` file:

```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

### 5. Create Database Tables

```bash
# Worker will auto-create tables on first run
python app/queue/workers/message_worker.py --type all
```

### 6. Start Worker

```bash
# In a separate terminal
cd backend
source venv/Scripts/activate  # Windows
python app/queue/workers/message_worker.py --type all
```

---

## 📊 Monitoring & Management

### Redis Monitoring

```bash
# Connect to Redis CLI
redis-cli

# Check all keys
KEYS *

# Get conversation state
GET conversation:1

# Get TTL
TTL conversation:1

# Delete key
DEL conversation:1

# Flush all
FLUSHDB
```

### RabbitMQ Monitoring

**Management UI:** http://localhost:15672

**CLI:**

```bash
# List queues
rabbitmqctl list_queues

# Check queue status
rabbitmqctl list_queues name messages consumers

# Purge queue
rabbitmqctl purge_queue chat_messages
```

**Python API:**

```python
from app.queue import get_rabbitmq_manager

mq = get_rabbitmq_manager()

# Get queue size
size = mq.get_queue_size('chat_messages')
print(f"Queue size: {size}")

# Purge queue
mq.purge_queue('chat_messages')
```

### Database Monitoring

```sql
-- Check message count
SELECT COUNT(*) FROM chat_message_logs;

-- Recent messages
SELECT * FROM chat_message_logs 
ORDER BY created_at DESC 
LIMIT 10;

-- Messages by intent
SELECT intent, COUNT(*) as count 
FROM chat_message_logs 
GROUP BY intent;

-- Preferences history
SELECT * FROM class_preference_logs 
WHERE student_id = 1 
ORDER BY created_at DESC;
```

---

## 🧪 Testing

See test files in `backend/app/tests/`:
- `test_redis_cache.py`
- `test_rabbitmq.py`
- `test_message_queue_service.py`

---

## ⚠️ Important Notes

### 1. TTL (Time To Live)

- **Redis:** 1 hour (adjustable)
- **RabbitMQ:** 24 hours for messages, 1 hour for preferences
- **Database:** Permanent storage

### 2. Error Handling

- Redis connection failure: System continues but no caching
- RabbitMQ connection failure: Logs error, doesn't crash
- Worker failure: Message requeued (max 3 retries)

### 3. Performance

- Redis: In-memory, very fast (<1ms)
- RabbitMQ: Disk-persisted, ~5-10ms
- Worker: Async processing, doesn't block API

### 4. Scaling

- **Redis:** Can use Redis Cluster for horizontal scaling
- **RabbitMQ:** Can run multiple workers
- **Worker:** Run multiple instances for load balancing

---

## 📚 References

- **Redis Documentation:** https://redis.io/docs/
- **RabbitMQ Documentation:** https://www.rabbitmq.com/documentation.html
- **Pika (Python RabbitMQ):** https://pika.readthedocs.io/

---

**Document Version:** 1.0  
**Last Updated:** December 2, 2025  
**Author:** Student Management System Team
