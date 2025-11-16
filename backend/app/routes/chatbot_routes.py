"""
Chatbot Routes - API endpoints cho chatbot with NL2SQL
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService
from app.schemas.chatbot_schema import (
    ChatMessage, 
    ChatResponse, 
    IntentsResponse, 
    IntentInfo,
    ChatResponseWithData
)
from app.db.database import get_db
from sqlalchemy import text


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize TF-IDF intent classifier and NL2SQL service
intent_classifier = TfidfIntentClassifier()
nl2sql_service = NL2SQLService()


@router.post("/chat", response_model=ChatResponseWithData)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """
    Endpoint nhận tin nhắn từ user và trả về phản hồi của chatbot kèm data từ database
    
    - **message**: Tin nhắn từ người dùng
    - **student_id**: ID sinh viên (optional, cho queries cần authentication)
    
    Returns:
        - **text**: Câu trả lời từ chatbot
        - **intent**: Intent được phân loại
        - **confidence**: Độ tin cậy (high/medium/low)
        - **data**: Dữ liệu từ database (nếu có)
        - **sql**: SQL query đã thực thi (nếu có)
    """
    try:
        # 1. Phân loại intent
        intent_result = await intent_classifier.classify_intent(message.message)
        
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # 2. Generate SQL and fetch data if applicable
        data = None
        sql_query = None
        sql_error = None
        
        # List of intents that need database query
        data_intents = [
            "grade_view", "learned_subjects_view", "subject_info", 
            "class_info", "schedule_view",
            "subject_registration_suggestion", "class_registration_suggestion"
        ]
        
        if intent in data_intents and confidence in ["high", "medium"]:
            try:
                print(f" DEBUG: student_id = {message.student_id}, intent = {intent}")
                
                # Generate SQL
                sql_result = await nl2sql_service.generate_sql(
                    question=message.message,
                    intent=intent,
                    student_id=message.student_id
                )
                
                print(f"DEBUG: SQL result = {sql_result}")
                
                sql_query = sql_result.get("sql")
                
                # Execute SQL if generated successfully
                if sql_query:
                    # Execute query
                    result = db.execute(text(sql_query))
                    rows = result.fetchall()
                    
                    # Convert to dict
                    if rows:
                        columns = result.keys()
                        data = [dict(zip(columns, row)) for row in rows]
                    else:
                        data = []
                    
                    # For class_registration_suggestion, add student CPA info
                    if intent == "class_registration_suggestion" and message.student_id:
                        try:
                            student_result = db.execute(text(
                                "SELECT cpa, failed_subjects_number, warning_level FROM students WHERE id = :student_id"
                            ), {"student_id": message.student_id}).fetchone()
                            
                            if student_result:
                                # Add student info to each class suggestion
                                for item in data:
                                    item["student_cpa"] = student_result[0]
                                    item["student_failed_subjects"] = student_result[1]
                                    item["student_warning_level"] = student_result[2]
                        except Exception as e:
                            print(f"   Warning: Could not fetch student CPA: {e}")
                
            except Exception as e:
                sql_error = str(e)
                print(f"   SQL execution error: {e}")
        
        # 3. Generate response text
        response_text = _generate_response_text(
            intent, 
            confidence, 
            intent_classifier, 
            data,
            sql_error
        )
        
        return ChatResponseWithData(
            text=response_text,
            intent=intent,
            confidence=confidence,
            data=data,
            sql=sql_query,
            sql_error=sql_error
        )
        
    except Exception as e:
        print(f"  Error in chatbot endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý tin nhắn: {str(e)}"
        )


def _generate_response_text(
    intent: str,
    confidence: str,
    classifier,
    data,
    sql_error: str = None
) -> str:
    """Generate response text based on intent, confidence and data"""
    
    # Handle SQL errors
    if sql_error:
        return f"Xin lỗi, có lỗi khi truy vấn dữ liệu: {sql_error}"
    
    # Handle low confidence
    if confidence == "low":
        return "Mình chưa hiểu rõ câu hỏi của bạn, bạn vui lòng diễn giải lại được không?"
    
    # Handle special intents
    if intent == "greeting":
        return "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?"
    
    if intent == "thanks":
        return "Rất vui được giúp đỡ bạn! Nếu có thắc mắc gì khác, hãy hỏi mình nhé 😊"
    
    # Handle data intents
    if data is not None:
        if len(data) == 0:
            return "Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."
        
        # Generate response based on intent and data
        if intent == "grade_view":
            return f"Thông tin học vụ của bạn:"
        elif intent == "learned_subjects_view":
            return f"Đây là điểm các môn đã học của bạn (tìm thấy {len(data)} môn):"
        elif intent == "student_info":
            return f"Đây là thông tin của bạn:"
        elif intent == "subject_info":
            return f"Thông tin về học phần (tìm thấy {len(data)} kết quả):"
        elif intent == "class_info":
            return f"Danh sách lớp học (tìm thấy {len(data)} lớp):"
        elif intent == "schedule_view":
            return f"Các môn/lớp bạn đã đăng ký (tìm thấy {len(data)} lớp):"
        elif intent == "subject_registration_suggestion":
            return f"Gợi ý các học phần nên đăng ký (tìm thấy {len(data)} học phần):"
        elif intent == "class_registration_suggestion":
            # Add CPA info if available
            cpa_info = ""
            if len(data) > 0 and "student_cpa" in data[0]:
                cpa = data[0]["student_cpa"]
                warning = data[0].get("student_warning_level", "")
                cpa_info = f" (CPA của bạn: {cpa:.2f}, {warning})"
            return f"Gợi ý các lớp học nên đăng ký (tìm thấy {len(data)} lớp){cpa_info}:"
    
    # Default response
    intent_friendly_name = classifier.get_intent_friendly_name(intent)
    return f"Bạn định {intent_friendly_name} phải không?"


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
