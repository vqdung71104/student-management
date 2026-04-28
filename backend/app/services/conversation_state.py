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
        conversation_id: Optional[int] = None,
        intent: str = 'class_registration_suggestion'
    ):
        self.student_id = student_id
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.intent = intent
        self.stage: str = 'initial'  # 'initial', 'collecting_preferences', 'generating_combinations', 'completed'
        self.preferences: CompletePreference = CompletePreference()
        self.questions_asked: list = []
        self.questions_remaining: list = []  # NEW: Track remaining questions
        self.current_question: Optional[PreferenceQuestion] = None
        self.pending_question: Optional[Dict] = None  # NEW: Pending question details
        self.nlq_constraints: Optional[Dict] = None  # Constraint extractor result (serialised)
        self.subject_source_choice: Optional[str] = 'suggested'  # 'registered' | 'suggested'
        self.subject_ids_seed: list = []
        self.supplemental_preference_keys: list = []
        self.timestamp: datetime = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'student_id': self.student_id,
            'session_id': self.session_id,
            'conversation_id': self.conversation_id,
            'intent': self.intent,
            'stage': self.stage,
            'preferences': self.preferences.dict(),
            'questions_asked': self.questions_asked,
            'questions_remaining': self.questions_remaining,
            'current_question': self.current_question.dict() if self.current_question else None,
            'pending_question': self.pending_question,
            'nlq_constraints': self.nlq_constraints,
            'subject_source_choice': self.subject_source_choice,
            'subject_ids_seed': self.subject_ids_seed,
            'supplemental_preference_keys': self.supplemental_preference_keys,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationState':
        """Create from dictionary"""
        state = cls(
            student_id=data['student_id'],
            session_id=data['session_id'],
            conversation_id=data.get('conversation_id', data['student_id']),
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
        state.nlq_constraints = data.get('nlq_constraints')
        state.subject_source_choice = data.get('subject_source_choice') or 'suggested'
        state.subject_ids_seed = data.get('subject_ids_seed', [])
        state.supplemental_preference_keys = data.get('supplemental_preference_keys', [])
        state.timestamp = datetime.fromisoformat(data['timestamp'])
        return state
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        """Check if state is expired"""
        return datetime.now() - self.timestamp > timedelta(minutes=ttl_minutes)


class ConversationStateManager:
    """Manages conversation states using in-memory storage (for testing/development)"""
    
    def __init__(self):
        # In-memory storage: {conversation_id: ConversationState}
        self._states: Dict[int, ConversationState] = {}
    
    def get_state(self, conversation_id: int) -> Optional[ConversationState]:
        """Get conversation state for conversation"""
        state = self._states.get(conversation_id)
        
        # Check if expired
        if state and state.is_expired():
            self.delete_state(conversation_id)
            return None
        
        return state
    
    def save_state(self, state: ConversationState):
        """Save conversation state"""
        if state.conversation_id is None:
            raise ValueError("conversation_id is required to save conversation state")
        state.timestamp = datetime.now()
        self._states[state.conversation_id] = state
    
    def delete_state(self, conversation_id: int):
        """Delete conversation state"""
        if conversation_id in self._states:
            del self._states[conversation_id]
    
    def has_active_conversation(self, conversation_id: int) -> bool:
        """Check if conversation has active conversation"""
        state = self.get_state(conversation_id)
        return state is not None and state.stage in [
            'initial',
            'collecting',
            'collecting_preferences',
            'generating_combinations',
            'choose_subject_source',
        ]


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
    
    def _get_key(self, conversation_id: int) -> str:
        """Generate Redis key for conversation"""
        return f"{self.key_prefix}:{conversation_id}"
    
    def get_conversation_state(self, conversation_id: int) -> Optional[ConversationState]:
        """
        Get conversation state from Redis
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            ConversationState or None if not found/expired
        """
        key = self._get_key(conversation_id)
        try:
            data = self.redis_cache.get(key)
        except Exception as e:
            print(f"⚠️ [REDIS] Read failed for conversation {conversation_id}, fallback to in-memory: {e}")
            return get_conversation_manager().get_state(conversation_id)
        
        if data:
            try:
                state = ConversationState.from_dict(data)
                if state.conversation_id is None:
                    state.conversation_id = conversation_id
                
                # Check if expired
                if state.is_expired(ttl_minutes=self.ttl_seconds // 60):
                    self.delete_conversation_state(conversation_id)
                    return None
                
                return state
            except Exception as e:
                print(f"❌ Error deserializing conversation state: {e}")
                return None
        
        return None
    
    def save_conversation_state(self, conversation_id: int, state: ConversationState):
        """
        Save conversation state to Redis
        
        Args:
            conversation_id: Conversation ID
            state: ConversationState to save
        """
        if state.conversation_id is None:
            state.conversation_id = conversation_id
        key = self._get_key(conversation_id)
        
        # Update timestamp
        state.timestamp = datetime.now()
        
        # Convert to dict and save with TTL
        data = state.to_dict()
        try:
            ok = self.redis_cache.set(key, data, ttl=self.ttl_seconds)
            if not ok:
                print(f"⚠️ [REDIS] Save returned False for conversation {conversation_id}, fallback to in-memory")
                get_conversation_manager().save_state(state)
                return
            print(f"💾 [REDIS] Saved conversation state for conversation {conversation_id}")
        except Exception as e:
            print(f"⚠️ [REDIS] Save failed for conversation {conversation_id}, fallback to in-memory: {e}")
            get_conversation_manager().save_state(state)
    
    def delete_conversation_state(self, conversation_id: int):
        """
        Delete conversation state from Redis

        Args:
            conversation_id: Conversation ID
        """
        key = self._get_key(conversation_id)
        try:
            self.redis_cache.delete(key)
            print(f"🗑️ [REDIS] Deleted conversation state for conversation {conversation_id}")
        except Exception as e:
            print(f"⚠️ [REDIS] Delete failed for conversation {conversation_id}, fallback cleanup in-memory: {e}")
        finally:
            # Always also clean up in-memory as a safety net
            get_conversation_manager().delete_state(conversation_id)

    def delete_state(self, conversation_id: int):
        """
        Alias for delete_conversation_state (backward compatibility).
        Removes conversation state from Redis with fallback to in-memory.

        Args:
            conversation_id: Conversation ID
        """
        self.delete_conversation_state(conversation_id)
    
    def has_active_conversation(self, conversation_id: int) -> bool:
        """
        Check if student has active conversation
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            True if active conversation exists
        """
        state = self.get_conversation_state(conversation_id)
        return state is not None and state.stage in ['initial', 'collecting_preferences', 'generating_combinations']
    
    def get_state(self, conversation_id: int) -> Optional[ConversationState]:
        """Alias for get_conversation_state (backward compatibility)"""
        return self.get_conversation_state(conversation_id)
    
    def save_state(self, state: ConversationState):
        """Alias for save_conversation_state (backward compatibility)"""
        if state.conversation_id is None:
            raise ValueError("conversation_id is required to save conversation state")
        self.save_conversation_state(state.conversation_id, state)


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


def get_conversation_state_manager():
    """
    Preferred manager accessor used by routes/services.
    Redis-first with automatic in-memory fallback.
    """
    return get_redis_conversation_manager()


def safe_delete_state(manager, conversation_id: int) -> bool:
    """
    Safely delete conversation state regardless of which manager is active.

    Handles the case where:
      - Redis manager doesn't have delete_state() (older version)
      - Redis is offline / raises exception during delete

    Returns True if deleted successfully, False otherwise.
    """
    try:
        if hasattr(manager, "delete_state"):
            manager.delete_state(conversation_id)
        elif hasattr(manager, "delete_conversation_state"):
            manager.delete_conversation_state(conversation_id)
        else:
            print(f"[STATE][WARN] Manager {type(manager).__name__} has no delete method — skipping cleanup.")
            return False
        return True
    except Exception as e:
        print(f"[STATE][WARN] Failed to delete conversation state {conversation_id}: {e}")
        return False
