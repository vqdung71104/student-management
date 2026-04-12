from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_history_model import ChatConversation, ChatMessage


class ChatHistoryService:
    """Persistence service for chatbot conversations and messages."""

    def __init__(self, db: Session):
        self.db = db
        self._cache = None
        self._cache_ready = False

    def _get_cache(self):
        if self._cache_ready:
            return self._cache

        self._cache_ready = True
        try:
            from app.cache.redis_cache import get_redis_cache

            self._cache = get_redis_cache()
        except Exception as exc:
            print(f"[CHAT_HISTORY] Redis unavailable, fallback to DB only: {exc}")
            self._cache = None

        return self._cache

    def _list_cache_key(self, student_pk: int, page: int, page_size: int) -> str:
        return f"chat:conv:list:{student_pk}:p:{page}:s:{page_size}"

    def _messages_cache_key(self, conversation_id: int, page: int, page_size: int) -> str:
        return f"chat:conv:msgs:{conversation_id}:p:{page}:s:{page_size}"

    def _log_metric(self, event: str, **fields: Any):
        payload = {"event": event, **fields}
        try:
            print(f"[CHAT_HISTORY_METRIC] {json.dumps(payload, default=str, ensure_ascii=False)}")
        except Exception:
            print(f"[CHAT_HISTORY_METRIC] {payload}")

    def _invalidate_list_cache(self, student_pk: int):
        cache = self._get_cache()
        if not cache:
            return

        keys = cache.get_keys(f"chat:conv:list:{student_pk}:*")
        for key in keys:
            cache.delete(key)

    def _invalidate_messages_cache(self, conversation_id: int):
        cache = self._get_cache()
        if not cache:
            return

        keys = cache.get_keys(f"chat:conv:msgs:{conversation_id}:*")
        for key in keys:
            cache.delete(key)

    @staticmethod
    def _normalize_title(first_message: Optional[str]) -> str:
        if not first_message:
            return "Cuoc tro chuyen moi"
        title = " ".join(first_message.strip().split())
        return title[:80] if title else "Cuoc tro chuyen moi"

    @staticmethod
    def _conversation_to_dict(conversation: ChatConversation) -> Dict[str, Any]:
        return {
            "id": int(conversation.id),
            "student_pk": int(conversation.student_pk),
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }

    @staticmethod
    def _message_to_dict(message: ChatMessage) -> Dict[str, Any]:
        return {
            "id": int(message.id),
            "conversation_id": int(message.conversation_id),
            "role": message.role,
            "content": message.content,
            "intent": message.intent,
            "confidence": message.confidence,
            "data_json": message.data_json,
            "sql_text": message.sql_text,
            "sql_error": message.sql_error,
            "created_at": message.created_at,
        }

    @staticmethod
    def _build_assistant_data_json(assistant_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = assistant_payload.get("data")
        is_compound = assistant_payload.get("is_compound")
        parts = assistant_payload.get("parts")
        metadata = assistant_payload.get("metadata")
        conversation_state_snapshot = assistant_payload.get("_conversation_state_snapshot")

        if data is None and not is_compound and not parts and not metadata and not conversation_state_snapshot:
            return None

        return {
            "data": data,
            "is_compound": bool(is_compound),
            "parts": parts,
            "metadata": metadata,
            "conversation_state_snapshot": conversation_state_snapshot,
        }

    def get_latest_assistant_message(self, student_pk: int, conversation_id: int) -> Optional[Dict[str, Any]]:
        conversation = (
            self.db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.student_pk == student_pk,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        message = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.role == "assistant",
            )
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .first()
        )

        if not message:
            return None

        return self._message_to_dict(message)

    def create_conversation(self, student_pk: int, title: Optional[str] = None) -> ChatConversation:
        conversation = ChatConversation(
            student_pk=student_pk,
            title=(title or "Cuoc tro chuyen moi")[:255],
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        self._invalidate_list_cache(student_pk)
        return conversation

    def get_or_create_conversation(
        self,
        student_pk: int,
        conversation_id: Optional[int],
        first_message: Optional[str] = None,
    ) -> ChatConversation:
        if conversation_id:
            conversation = (
                self.db.query(ChatConversation)
                .filter(
                    ChatConversation.id == conversation_id,
                    ChatConversation.student_pk == student_pk,
                )
                .first()
            )
            if not conversation:
                raise ValueError("Conversation not found or access denied")
            return conversation

        title = self._normalize_title(first_message)
        return self.create_conversation(student_pk=student_pk, title=title)

    def save_chat_turn(
        self,
        student_pk: int,
        user_content: str,
        assistant_payload: Dict[str, Any],
        conversation_id: Optional[int] = None,
    ) -> Tuple[ChatConversation, ChatMessage, ChatMessage]:
        conversation = self.get_or_create_conversation(
            student_pk=student_pk,
            conversation_id=conversation_id,
            first_message=user_content,
        )

        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=user_content,
        )
        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_payload.get("text") or "",
            intent=assistant_payload.get("intent"),
            confidence=assistant_payload.get("confidence"),
            data_json=self._build_assistant_data_json(assistant_payload),
            sql_text=assistant_payload.get("sql"),
            sql_error=assistant_payload.get("sql_error"),
        )

        conversation.updated_at = datetime.utcnow()

        self.db.add(user_msg)
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(user_msg)
        self.db.refresh(assistant_msg)

        self._invalidate_list_cache(student_pk)
        self._invalidate_messages_cache(conversation.id)

        return conversation, user_msg, assistant_msg

    def list_conversations(
        self,
        student_pk: int,
        page: int = 1,
        page_size: int = 20,
        ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        cache = self._get_cache()
        key = self._list_cache_key(student_pk, page, page_size)

        if cache:
            cached = cache.get(key)
            if cached:
                cached["cache_hit"] = True
                self._log_metric(
                    "conversation_list",
                    cache_hit=True,
                    student_pk=student_pk,
                    page=page,
                    page_size=page_size,
                    rows=len(cached.get("items", [])),
                    elapsed_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
                return cached

        offset = (page - 1) * page_size
        total = (
            self.db.query(func.count(ChatConversation.id))
            .filter(ChatConversation.student_pk == student_pk)
            .scalar()
        )

        rows = (
            self.db.query(ChatConversation)
            .filter(ChatConversation.student_pk == student_pk)
            .order_by(ChatConversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        payload = {
            "total": int(total or 0),
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(rows) < int(total or 0),
            "items": [self._conversation_to_dict(row) for row in rows],
            "cache_hit": False,
        }

        if cache:
            cache.set(key, payload, ttl_seconds)

        self._log_metric(
            "conversation_list",
            cache_hit=False,
            student_pk=student_pk,
            page=page,
            page_size=page_size,
            rows=len(rows),
            elapsed_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )

        return payload

    def list_messages(
        self,
        student_pk: int,
        conversation_id: int,
        page: int = 1,
        page_size: int = 50,
        ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        conversation = (
            self.db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.student_pk == student_pk,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        cache = self._get_cache()
        key = self._messages_cache_key(conversation_id, page, page_size)

        if cache:
            cached = cache.get(key)
            if cached:
                cached["cache_hit"] = True
                self._log_metric(
                    "conversation_messages",
                    cache_hit=True,
                    student_pk=student_pk,
                    conversation_id=conversation_id,
                    page=page,
                    page_size=page_size,
                    rows=len(cached.get("items", [])),
                    elapsed_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
                return cached

        offset = (page - 1) * page_size
        total = (
            self.db.query(func.count(ChatMessage.id))
            .filter(ChatMessage.conversation_id == conversation_id)
            .scalar()
        )

        rows = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        rows = list(reversed(rows))

        payload = {
            "conversation": self._conversation_to_dict(conversation),
            "total": int(total or 0),
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(rows) < int(total or 0),
            "items": [self._message_to_dict(row) for row in rows],
            "cache_hit": False,
        }

        if cache:
            cache.set(key, payload, ttl_seconds)

        self._log_metric(
            "conversation_messages",
            cache_hit=False,
            student_pk=student_pk,
            conversation_id=conversation_id,
            page=page,
            page_size=page_size,
            rows=len(rows),
            elapsed_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )

        return payload

    def rename_conversation(self, student_pk: int, conversation_id: int, title: str) -> ChatConversation:
        conversation = (
            self.db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.student_pk == student_pk,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        conversation.title = title[:255]
        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)

        self._invalidate_list_cache(student_pk)
        self._invalidate_messages_cache(conversation_id)

        return conversation

    def delete_conversation(self, student_pk: int, conversation_id: int):
        conversation = (
            self.db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.student_pk == student_pk,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        self.db.delete(conversation)
        self.db.commit()

        try:
            from app.services.conversation_state import get_conversation_state_manager

            get_conversation_state_manager().delete_state(conversation_id)
        except Exception as exc:
            print(f"[CHAT_HISTORY] Failed to clear conversation state for conversation {conversation_id}: {exc}")

        self._invalidate_list_cache(student_pk)
        self._invalidate_messages_cache(conversation_id)
