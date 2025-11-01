"""
Chatbot Routes - API endpoints cho chatbot
"""
from fastapi import APIRouter, HTTPException
from app.chatbot.hybrid_classifier import HybridIntentClassifier
from app.schemas.chatbot_schema import ChatMessage, ChatResponse, IntentsResponse, IntentInfo


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize hybrid intent classifier (PhoBERT + Gemini)
intent_classifier = HybridIntentClassifier(use_phobert=True, use_gemini=True)


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


@router.get("/intents", response_model=IntentsResponse)
async def get_available_intents():
    """
    Lấy danh sách các intent mà chatbot có thể nhận diện
    
    Returns:
        IntentsResponse: Danh sách các intent với tag, description và examples
    """
    try:
        intents_list = []
        for intent in intent_classifier.intents.get("intents", []):
            intents_list.append(
                IntentInfo(
                    tag=intent["tag"],
                    description=intent["description"],
                    examples=intent["patterns"][:3]  # Lấy 3 ví dụ
                )
            )
        
        return IntentsResponse(
            total=len(intents_list),
            intents=intents_list
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi lấy danh sách intent: {str(e)}"
        )
