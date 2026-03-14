from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, ForeignKey, JSON, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_pk = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_chat_conv_student_updated", "student_pk", "updated_at"),
        Index("idx_chat_conv_updated", "updated_at"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(
        BigInteger,
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(Enum("user", "assistant", "system", name="chat_message_role"), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True)
    confidence = Column(String(16), nullable=True)
    data_json = Column(JSON, nullable=True)
    sql_text = Column(Text, nullable=True)
    sql_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    conversation = relationship("ChatConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_chat_msg_conv_created", "conversation_id", "created_at"),
    )
