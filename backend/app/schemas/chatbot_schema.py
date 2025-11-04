"""
Chatbot Schemas - Pydantic models cho chatbot API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Schema cho tin nhắn chat từ user"""
    message: str = Field(..., description="Tin nhắn từ người dùng", min_length=1)
    student_id: Optional[int] = Field(None, description="ID sinh viên (optional, dùng cho queries cần authentication)")
    
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
