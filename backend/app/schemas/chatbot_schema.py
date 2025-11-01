"""
Chatbot Schemas - Pydantic models cho chatbot API
"""
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Schema cho tin nhắn chat từ user"""
    message: str = Field(..., description="Tin nhắn từ người dùng", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Làm sao để đăng ký môn học?"
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
