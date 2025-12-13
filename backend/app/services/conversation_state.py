"""
Conversation State Management for Interactive Preference Collection
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
from app.schemas.preference_schema import CompletePreference, PreferenceQuestion


class ConversationState:
    """Represents conversation state for preference collection"""
    
    def __init__(
        self, 
        student_id: int,
        session_id: str,
        intent: str = 'class_registration_suggestion'
    ):
        self.student_id = student_id
        self.session_id = session_id
        self.intent = intent
        self.stage: str = 'initial'  # 'initial', 'collecting_preferences', 'generating_combinations', 'completed'
        self.preferences: CompletePreference = CompletePreference()
        self.questions_asked: list = []
        self.questions_remaining: list = []  # NEW: Track remaining questions
        self.current_question: Optional[PreferenceQuestion] = None
        self.pending_question: Optional[Dict] = None  # NEW: Pending question details
        self.timestamp: datetime = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'student_id': self.student_id,
            'session_id': self.session_id,
            'intent': self.intent,
            'stage': self.stage,
            'preferences': self.preferences.dict(),
            'questions_asked': self.questions_asked,
            'questions_remaining': self.questions_remaining,
            'current_question': self.current_question.dict() if self.current_question else None,
            'pending_question': self.pending_question,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationState':
        """Create from dictionary"""
        state = cls(
            student_id=data['student_id'],
            session_id=data['session_id'],
            intent=data['intent']
        )
        state.stage = data['stage']
        state.preferences = CompletePreference(**data['preferences'])
        state.questions_asked = data['questions_asked']
        state.questions_remaining = data.get('questions_remaining', [])
        if data.get('current_question'):
            from app.schemas.preference_schema import PreferenceQuestion
            state.current_question = PreferenceQuestion(**data['current_question'])
        state.pending_question = data.get('pending_question')
        state.timestamp = datetime.fromisoformat(data['timestamp'])
        return state
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        """Check if state is expired"""
        return datetime.now() - self.timestamp > timedelta(minutes=ttl_minutes)


class ConversationStateManager:
    """Manages conversation states using in-memory storage (for testing/development)"""
    
    def __init__(self):
        # In-memory storage: {student_id: ConversationState}
        self._states: Dict[int, ConversationState] = {}
    
    def get_state(self, student_id: int) -> Optional[ConversationState]:
        """Get conversation state for student"""
        state = self._states.get(student_id)
        
        # Check if expired
        if state and state.is_expired():
            self.delete_state(student_id)
            return None
        
        return state
    
    def save_state(self, state: ConversationState):
        """Save conversation state"""
        state.timestamp = datetime.now()
        self._states[state.student_id] = state
    
    def delete_state(self, student_id: int):
        """Delete conversation state"""
        if student_id in self._states:
            del self._states[student_id]
    
    def has_active_conversation(self, student_id: int) -> bool:
        """Check if student has active conversation"""
        state = self.get_state(student_id)
        return state is not None and state.stage in ['initial', 'collecting']


# Global instance (in-memory for development)
_conversation_manager = ConversationStateManager()


def get_conversation_manager() -> ConversationStateManager:
    """Get global conversation manager instance (in-memory)"""
    return _conversation_manager


# ============================================================================
# Redis-based Conversation State Manager (Phase 4 Implementation)
# ============================================================================

class RedisConversationStateManager:
    """
    Manages conversation states using Redis storage
    Implements Phase 4 design from INTERACTIVE_CLASS_SUGGESTION_DESIGN.md
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize Redis-based state manager
        
        Args:
            ttl_seconds: Time to live for conversation states (default: 1 hour)
        """
        from app.cache.redis_cache import get_redis_cache
        self.redis_cache = get_redis_cache()
        self.ttl_seconds = ttl_seconds
        self.key_prefix = "conversation:class_suggestion"
    
    def _get_key(self, student_id: int) -> str:
        """Generate Redis key for student conversation"""
        return f"{self.key_prefix}:{student_id}"
    
    def get_conversation_state(self, student_id: int) -> Optional[ConversationState]:
        """
        Get conversation state from Redis
        
        Args:
            student_id: Student ID
        
        Returns:
            ConversationState or None if not found/expired
        """
        key = self._get_key(student_id)
        data = self.redis_cache.get(key)
        
        if data:
            try:
                state = ConversationState.from_dict(data)
                
                # Check if expired
                if state.is_expired(ttl_minutes=self.ttl_seconds // 60):
                    self.delete_conversation_state(student_id)
                    return None
                
                return state
            except Exception as e:
                print(f"❌ Error deserializing conversation state: {e}")
                return None
        
        return None
    
    def save_conversation_state(self, student_id: int, state: ConversationState):
        """
        Save conversation state to Redis
        
        Args:
            student_id: Student ID
            state: ConversationState to save
        """
        key = self._get_key(student_id)
        
        # Update timestamp
        state.timestamp = datetime.now()
        
        # Convert to dict and save with TTL
        data = state.to_dict()
        self.redis_cache.set(key, data, ttl=self.ttl_seconds)
        
        print(f"💾 [REDIS] Saved conversation state for student {student_id}")
    
    def delete_conversation_state(self, student_id: int):
        """
        Delete conversation state from Redis
        
        Args:
            student_id: Student ID
        """
        key = self._get_key(student_id)
        self.redis_cache.delete(key)
        print(f"🗑️ [REDIS] Deleted conversation state for student {student_id}")
    
    def has_active_conversation(self, student_id: int) -> bool:
        """
        Check if student has active conversation
        
        Args:
            student_id: Student ID
        
        Returns:
            True if active conversation exists
        """
        state = self.get_conversation_state(student_id)
        return state is not None and state.stage in ['initial', 'collecting_preferences', 'generating_combinations']
    
    def get_state(self, student_id: int) -> Optional[ConversationState]:
        """Alias for get_conversation_state (backward compatibility)"""
        return self.get_conversation_state(student_id)
    
    def save_state(self, state: ConversationState):
        """Alias for save_conversation_state (backward compatibility)"""
        self.save_conversation_state(state.student_id, state)


# Global Redis-based manager instance
_redis_conversation_manager: Optional[RedisConversationStateManager] = None


def get_redis_conversation_manager() -> RedisConversationStateManager:
    """
    Get global Redis conversation manager instance
    
    Returns:
        RedisConversationStateManager instance
    """
    global _redis_conversation_manager
    
    if _redis_conversation_manager is None:
        try:
            _redis_conversation_manager = RedisConversationStateManager()
            print("✅ Redis Conversation State Manager initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Redis manager: {e}")
            print("⚠️ Falling back to in-memory manager")
            # Return in-memory manager as fallback
            return get_conversation_manager()
    
    return _redis_conversation_manager
