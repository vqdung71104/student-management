"""
Chatbot Routes - API endpoints cho chatbot with NL2SQL and Rule Engine
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService
from app.services.chatbot_service import ChatbotService
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
        # Initialize chatbot service
        chatbot_service = ChatbotService(db)
        
        # CRITICAL: Check for active conversation state BEFORE intent classification
        # If user is in the middle of answering preference questions, skip intent classification
        from app.services.conversation_state import get_conversation_manager
        conv_manager = get_conversation_manager()
        state = conv_manager.get_state(message.student_id)
        
        if state and state.stage == 'collecting':
            # User is answering a preference question - directly process as class_registration_suggestion
            print(f"🔄 [ROUTE] Active conversation detected for student {message.student_id}, skipping intent classification")
            result = await chatbot_service.process_class_suggestion(
                student_id=message.student_id,
                question=message.message
            )
            return ChatResponseWithData(
                text=result["text"],
                intent=result["intent"],
                confidence=result["confidence"],
                data=result.get("data"),
                sql=None,
                sql_error=result.get("error")
            )
        
        # 1. Phân loại intent (only if NOT in active conversation)
        intent_result = await intent_classifier.classify_intent(message.message)
        
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # 2. Check if intent uses Rule Engine
        rule_engine_intents = ["subject_registration_suggestion", "class_registration_suggestion"]
        
        if intent in rule_engine_intents and confidence in ["high", "medium"]:
            # Use Rule Engine for intelligent suggestions
            if intent == "subject_registration_suggestion":
                result = await chatbot_service.process_subject_suggestion(
                    student_id=message.student_id,
                    question=message.message
                )
                return ChatResponseWithData(
                    text=result["text"],
                    intent=result["intent"],
                    confidence=result["confidence"],
                    data=result.get("data"),
                    sql=None,
                    sql_error=result.get("error")
                )
            
            elif intent == "class_registration_suggestion":
                result = await chatbot_service.process_class_suggestion(
                    student_id=message.student_id,
                    question=message.message
                )
                return ChatResponseWithData(
                    text=result["text"],
                    intent=result["intent"],
                    confidence=result["confidence"],
                    data=result.get("data"),
                    sql=None,
                    sql_error=result.get("error")
                )
        
        # 3. Use NL2SQL for other data intents
        data = None
        sql_query = None
        sql_error = None
        
        # List of intents that need database query via NL2SQL
        nl2sql_intents = [
            "grade_view", "learned_subjects_view", "subject_info", 
            "class_info", "schedule_view"
        ]
        
        if intent in nl2sql_intents and confidence in ["high", "medium"]:
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
                    
            except Exception as e:
                sql_error = str(e)
                print(f"   SQL execution error: {e}")
        
        # 4. Generate response text
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


@router.post("/export-schedule")
async def export_schedule_to_excel(request_data: dict):
    """
    Export schedule combination to Excel file
    
    Request body:
    {
        "combination": { ... },  // Combination data from chatbot response
        "student_info": { ... }  // Student info for header (optional)
    }
    
    Returns:
        Excel file (.xlsx) as StreamingResponse
    """
    try:
        from fastapi.responses import StreamingResponse
        from app.services.excel_export_service import ExcelExportService
        
        combination = request_data.get("combination")
        student_info = request_data.get("student_info", {})
        
        if not combination:
            raise HTTPException(
                status_code=400,
                detail="Missing combination data"
            )
        
        # Generate Excel file
        excel_service = ExcelExportService()
        excel_file = excel_service.generate_excel(combination, student_info)
        
        # Create filename
        combination_id = combination.get('combination_id', 1)
        filename = f"Phuong_An_{combination_id}_Lich_Hoc.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        print(f"❌ [EXCEL_EXPORT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xuất file Excel: {str(e)}"
        )
