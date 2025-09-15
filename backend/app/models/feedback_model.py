from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class FeedbackStatus(enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"

class FeedbackSubject(enum.Enum):
    BUG = "bug"
    FEATURE = "feature"
    UI = "ui"
    PERFORMANCE = "performance"
    CONTENT = "content"
    OTHER = "other"

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    subject = Column(Enum(FeedbackSubject), nullable=False)
    feedback = Column(Text, nullable=False)
    suggestions = Column(Text, nullable=True)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())