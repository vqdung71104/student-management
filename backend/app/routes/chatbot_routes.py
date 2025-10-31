"""
Chatbot Routes - API endpoints cho chatbot
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.chatbot.intent_classifier import IntentClassifier


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize intent classifier
intent_classifier = IntentClassifier()


class ChatMessage(BaseModel):
    """Schema cho tin nhắn chat"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Làm sao để đăng ký môn học?"
            }
        }


class ChatResponse(BaseModel):
    """Schema cho response từ chatbot"""
    text: str
    intent: str
    confidence: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Bạn định hướng dẫn đăng ký học phần phải không?",
                "intent": "registration_guide",
                "confidence": "high"
            }
        }


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Endpoint nhận tin nhắn từ user và trả về phản hồi của chatbot
    
    - **message**: Tin nhắn từ người dùng
    
    Returns:
        - **text**: Câu trả lời từ chatbot
        - **intent**: Intent được phân loại
        - **confidence**: Độ tin cậy (high/low)
    """
    try:
        # Phân loại intent
        result = await intent_classifier.classify_intent(message.message)
        
        intent = result["intent"]
        confidence = result["confidence"]
        
        # Tạo response text dựa trên intent và confidence
        if confidence == "high" and intent != "unknown":
            # Xử lý các intent đặc biệt
            if intent == "greeting":
                response_text = "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?"
            elif intent == "thanks":
                response_text = "Rất vui được giúp đỡ bạn! Nếu có thắc mắc gì khác, hãy hỏi mình nhé 😊"
            else:
                # Intent thông thường
                intent_friendly_name = intent_classifier.get_intent_friendly_name(intent)
                response_text = f"Bạn định {intent_friendly_name} phải không?"
        else:
            # Không hiểu ý định
            response_text = "Mình chưa hiểu rõ câu hỏi của bạn, bạn vui lòng diễn giải lại được không?"
        
        return ChatResponse(
            text=response_text,
            intent=intent,
            confidence=confidence
        )
        
    except Exception as e:
        print(f"Lỗi trong chatbot endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý tin nhắn: {str(e)}"
        )


@router.get("/intents")
async def get_available_intents():
    """
    Lấy danh sách các intent mà chatbot có thể nhận diện
    
    Returns:
        List các intent với tag và description
    """
    try:
        intents_list = []
        for intent in intent_classifier.intents.get("intents", []):
            intents_list.append({
                "tag": intent["tag"],
                "description": intent["description"],
                "examples": intent["patterns"][:3]  # Lấy 3 ví dụ
            })
        
        return {
            "total": len(intents_list),
            "intents": intents_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi lấy danh sách intent: {str(e)}"
        )
