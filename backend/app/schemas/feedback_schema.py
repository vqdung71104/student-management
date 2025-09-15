from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class FeedbackStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"

class FeedbackSubject(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    UI = "ui"
    PERFORMANCE = "performance"
    CONTENT = "content"
    OTHER = "other"

class FeedbackBase(BaseModel):
    email: EmailStr
    subject: FeedbackSubject
    feedback: str
    suggestions: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatus] = None

class FeedbackBulkUpdate(BaseModel):
    feedback_ids: list[int]
    status: FeedbackStatus

class FeedbackResponse(FeedbackBase):
    id: int
    status: FeedbackStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FAQBase(BaseModel):
    question: str
    answer: str
    is_active: bool = True
    order_index: int = 0

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None

class FAQResponse(FAQBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True