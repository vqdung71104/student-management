"""
Chatbot Schemas - Pydantic models cho chatbot API
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Schema cho tin nhắn chat từ user"""
    message: str = Field(..., description="Tin nhắn từ người dùng", min_length=1)
    student_id: Optional[int] = Field(None, description="ID sinh viên (optional, dùng cho queries cần authentication)")
    conversation_id: Optional[int] = Field(None, description="ID hội thoại (optional, backend tự tạo nếu không gửi)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Làm sao để đăng ký môn học?",
                "student_id": 1
            }
        }


class ChatResponse(BaseModel):
    """Schema cho response từ chatbot"""
    text: str = Field(..., description="Câu trả lời từ chatbot")
    intent: str = Field(..., description="Intent được phân loại")
    confidence: str = Field(..., description="Độ tin cậy: high, medium, low")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Bạn định hướng dẫn đăng ký học phần phải không?",
                "intent": "registration_guide",
                "confidence": "high"
            }
        }


class ChatResponseWithData(ChatResponse):
    """Schema cho response từ chatbot kèm data từ database"""
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Dữ liệu từ database")
    sql: Optional[str] = Field(None, description="SQL query đã thực thi")
    sql_error: Optional[str] = Field(None, description="Lỗi SQL (nếu có)")
    is_compound: bool = Field(False, description="True nếu câu hỏi là compound query (nhiều intent)")
    parts: Optional[List[Dict[str, Any]]] = Field(None, description="Kết quả từng phần khi is_compound=True")
    conversation_id: Optional[int] = Field(None, description="ID hội thoại đã lưu")
    message_id: Optional[int] = Field(None, description="ID bản ghi assistant message")
    created_at: Optional[datetime] = Field(None, description="Thời gian lưu assistant message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Đây là điểm của bạn (tìm thấy 5 môn học):",
                "intent": "grade_view",
                "confidence": "high",
                "data": [
                    {
                        "subject_name": "Giải tích 1",
                        "credits": 4,
                        "letter_grade": "A",
                        "semester": "2024.1"
                    }
                ],
                "sql": "SELECT ls.subject_name, ls.credits, ls.letter_grade, ls.semester FROM learned_subjects ls WHERE ls.student_id = 1",
                "sql_error": None
            }
        }


class IntentInfo(BaseModel):
    """Schema cho thông tin một intent"""
    tag: str = Field(..., description="Tag của intent")
    description: str = Field(..., description="Mô tả intent")
    examples: list[str] = Field(..., description="Các ví dụ patterns")


class IntentsResponse(BaseModel):
    """Schema cho danh sách các intent"""
    total: int = Field(..., description="Tổng số intent")
    intents: list[IntentInfo] = Field(..., description="Danh sách các intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 7,
                "intents": [
                    {
                        "tag": "registration_guide",
                        "description": "Hướng dẫn quy trình đăng ký học phần",
                        "examples": [
                            "hướng dẫn đăng ký học phần",
                            "cách đăng ký môn học",
                            "đăng ký học phần như thế nào"
                        ]
                    }
                ]
            }
        }


class ConversationCreateRequest(BaseModel):
    student_id: int = Field(..., description="ID sinh viên")
    title: Optional[str] = Field(None, description="Tiêu đề hội thoại", max_length=255)


class ConversationUpdateRequest(BaseModel):
    student_id: int = Field(..., description="ID sinh viên")
    title: str = Field(..., description="Tiêu đề mới", min_length=1, max_length=255)


class ChatConversationItem(BaseModel):
    id: int
    student_pk: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChatConversationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    has_more: bool = False
    items: List[ChatConversationItem]
    cache_hit: bool = False


class ChatHistoryMessageItem(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    intent: Optional[str] = None
    confidence: Optional[str] = None
    data_json: Optional[Any] = None
    sql_text: Optional[str] = None
    sql_error: Optional[str] = None
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation: ChatConversationItem
    total: int
    page: int
    page_size: int
    has_more: bool = False
    items: List[ChatHistoryMessageItem]
    cache_hit: bool = False
