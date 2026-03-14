"""
Chatbot Routes - API endpoints cho chatbot with NL2SQL and Rule Engine
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService
from app.services.chatbot_service import ChatbotService
from app.services.text_preprocessor import get_text_preprocessor
from app.services.query_splitter import get_query_splitter, SubQuery
from app.services.chat_history_service import ChatHistoryService
from app.schemas.chatbot_schema import (
    ChatMessage, 
    IntentsResponse, 
    IntentInfo,
    ChatResponseWithData,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ChatConversationItem,
    ChatConversationListResponse,
    ConversationMessagesResponse,
)
from app.db.database import get_db
from sqlalchemy import text


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize TF-IDF intent classifier, NL2SQL service, and text preprocessor
intent_classifier = TfidfIntentClassifier()
nl2sql_service = NL2SQLService()
text_preprocessor = get_text_preprocessor()
query_splitter = get_query_splitter()


# ─────────────────────────────────────────────────────────────────────────────
# Section header helper
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_HEADERS = {
    "grade_view":                    "📊 Điểm học tập",
    "learned_subjects_view":         "📋 Các môn đã học / môn trượt",
    "subject_info":                  "📚 Thông tin học phần",
    "class_info":                    "🏫 Danh sách lớp học",
    "schedule_view":                 "📅 Thời khóa biểu",
    "subject_registration_suggestion": "💡 Gợi ý môn học nên đăng ký",
    "class_registration_suggestion": "🗓️ Gợi ý lớp học phù hợp",
    "student_info":                  "👤 Thông tin sinh viên",
}


def _section_header(intent: str) -> str:
    return _SECTION_HEADERS.get(intent, f"ℹ️ {intent}")


# ─────────────────────────────────────────────────────────────────────────────
# Merge helper
# ─────────────────────────────────────────────────────────────────────────────

def _merge_responses(
    parts: List[ChatResponseWithData],
    sub_queries: List[SubQuery],
) -> ChatResponseWithData:
    """
    Merge multiple single-intent responses into one compound response.
    - text: empty, since frontend will render each part sequentially
    - data: all items merged, each tagged with _intent_type
    - parts: list of part dicts for frontend to render separately
    """
    merged_data: List = []
    parts_list: List = []

    for resp, sq in zip(parts, sub_queries):
        header = _section_header(resp.intent)
        part_text = f"**{header}**\n{resp.text}"

        if resp.data:
            for item in resp.data:
                tagged = dict(item)
                tagged["_intent_type"] = resp.intent
                merged_data.append(tagged)

        parts_list.append({
            "intent": resp.intent,
            "confidence": resp.confidence,
            "text": part_text,
            "data": resp.data,
            "sql_error": resp.sql_error,
            "query": sq.text,
        })

    return ChatResponseWithData(
        text="Dưới đây là thông tin chi tiết cho từng phần trong câu hỏi của bạn:",
        intent="compound",
        confidence="high",
        data=merged_data if merged_data else None,
        sql=None,
        sql_error=None,
        is_compound=True,
        parts=parts_list,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Single-query processor  (extracted from the main handler)
# ─────────────────────────────────────────────────────────────────────────────

async def _process_single_query(
    normalized_text: str,
    student_id: Optional[int],
    db: Session,
    chatbot_service: ChatbotService,
) -> ChatResponseWithData:
    """Process one normalized sub-query and return ChatResponseWithData."""

    # ── Intent classification ─────────────────────────────────────────────────
    intent_result = await intent_classifier.classify_intent(normalized_text)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]

    # ── Rule-engine intents ───────────────────────────────────────────────────
    if intent in ("subject_registration_suggestion", "class_registration_suggestion") \
            and confidence in ("high", "medium"):
        if intent == "subject_registration_suggestion":
            result = await chatbot_service.process_subject_suggestion(
                student_id=student_id,
                question=normalized_text,
            )
        else:
            result = await chatbot_service.process_class_suggestion(
                student_id=student_id,
                question=normalized_text,
            )
        return ChatResponseWithData(
            text=result["text"],
            intent=result["intent"],
            confidence=result["confidence"],
            data=result.get("data"),
            sql=None,
            sql_error=result.get("error"),
        )

    # ── class_info: constraint extractor first ────────────────────────────────
    if intent == "class_info" and confidence in ("high", "medium"):
        try:
            from app.services.constraint_extractor import get_constraint_extractor
            from app.services.class_query_service import ClassQueryService
            extractor = get_constraint_extractor()
            constraints = extractor.extract(normalized_text, query_type="class_info")
            if constraints.subject_codes or constraints.subject_names:
                print(f"🔍 [CLASS_INFO] codes={constraints.subject_codes} names={constraints.subject_names}")
                svc = ClassQueryService(db)
                rows = svc.query(constraints)
                if rows:
                    import datetime
                    for r in rows:
                        if isinstance(r.get("study_time_start"), datetime.time):
                            r["study_time_start"] = r["study_time_start"].strftime("%H:%M")
                        if isinstance(r.get("study_time_end"), datetime.time):
                            r["study_time_end"] = r["study_time_end"].strftime("%H:%M")
                    return ChatResponseWithData(
                        text=f"✅ Tìm thấy {len(rows)} lớp học phù hợp.",
                        intent="class_info",
                        confidence="high",
                        data=rows,
                        sql=None,
                        sql_error=None,
                    )
        except Exception as ce:
            print(f"⚠️ [CLASS_INFO] Constraint path error: {ce}")

    # ── NL2SQL path ───────────────────────────────────────────────────────────
    data = None
    sql_query = None
    sql_error = None

    nl2sql_intents = [
        "grade_view", "learned_subjects_view", "subject_info",
        "class_info", "schedule_view",
    ]

    if intent in nl2sql_intents and confidence in ("high", "medium"):
        try:
            print(f"🔎 [NL2SQL] student_id={student_id} intent={intent}")
            sql_result = await nl2sql_service.generate_sql(
                question=normalized_text,
                intent=intent,
                student_id=student_id,
                db=db,
            )
            print(f"🔎 [NL2SQL] result={sql_result}")

            # Fuzzy clarification
            fuzzy_info = sql_result.get("fuzzy_match")
            if fuzzy_info and not fuzzy_info.get("auto_mapped", True):
                try:
                    import re as _re
                    original_query = fuzzy_info["original_query"]
                    is_subject_code = bool(_re.match(r'^[A-Z]{2,4}\d{3,4}[A-Z]?$', original_query.upper()))
                    if is_subject_code and fuzzy_info.get("matched_id"):
                        matched_id   = fuzzy_info["matched_id"]
                        matched_name = fuzzy_info["matched_name"]
                        score        = fuzzy_info["score"]
                        clarification_text = (
                            f"🔍 Không tìm thấy môn **{original_query}**.\n"
                            f"Bạn có muốn hỏi về môn **{matched_name} ({matched_id})**"
                            f" (độ tương đồng {score:.0f}%) không?\n"
                            f"Hãy nhập lại với mã môn **{matched_id}** hoặc tên môn đầy đủ."
                        )
                    else:
                        from app.services.fuzzy_matcher import FuzzyMatcher
                        matcher = FuzzyMatcher(db)
                        candidates = matcher.get_subject_candidates(original_query, db=db)
                        clarification_text = matcher.format_candidates_prompt(candidates)
                    return ChatResponseWithData(
                        text=clarification_text,
                        intent=intent,
                        confidence="medium",
                        data=None,
                        sql=None,
                        sql_error=None,
                    )
                except Exception as fe:
                    print(f"⚠️ Fuzzy clarification error: {fe}")

            sql_query = sql_result.get("sql")
            if sql_query:
                result_rows = db.execute(text(sql_query))
                rows = result_rows.fetchall()
                if rows:
                    columns = result_rows.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
        except Exception as e:
            sql_error = str(e)
            print(f"⚠️ SQL execution error: {e}")

    # ── Response text ─────────────────────────────────────────────────────────
    response_text = _generate_response_text(intent, confidence, intent_classifier, data, sql_error)

    return ChatResponseWithData(
        text=response_text,
        intent=intent,
        confidence=confidence,
        data=data,
        sql=sql_query,
        sql_error=sql_error,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main chat endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponseWithData)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """
    Endpoint nhận tin nhắn từ user và trả về phản hồi của chatbot kèm data từ database

    - **message**: Tin nhắn từ người dùng
    - **student_id**: ID sinh viên (optional, cho queries cần authentication)

    Returns:
        - **text**: Câu trả lời từ chatbot
        - **intent**: Intent được phân loại (hoặc "compound" nếu multi-intent)
        - **confidence**: Độ tin cậy (high/medium/low)
        - **data**: Dữ liệu từ database (nếu có)
        - **is_compound**: True nếu câu hỏi chứa nhiều intent
        - **parts**: List kết quả từng phần (khi is_compound=True)
    """
    try:
        chatbot_service = ChatbotService(db)
        history_service = ChatHistoryService(db)
        response_payload: ChatResponseWithData

        # ── Active conversation shortcut (preference collection in progress) ──
        from app.services.conversation_state import get_conversation_manager
        conv_manager = get_conversation_manager()
        state = conv_manager.get_state(message.student_id)

        if state and state.stage == 'collecting':
            print(f"🔄 [ROUTE] Active conversation for student {message.student_id}")
            normalized_message = text_preprocessor.preprocess(message.message)
            result = await chatbot_service.process_class_suggestion(
                student_id=message.student_id,
                question=normalized_message,
            )
            response_payload = ChatResponseWithData(
                text=result["text"],
                intent=result["intent"],
                confidence=result["confidence"],
                data=result.get("data"),
                sql=None,
                sql_error=result.get("error"),
            )
            if message.student_id:
                try:
                    conversation, _, assistant_message = history_service.save_chat_turn(
                        student_pk=message.student_id,
                        user_content=message.message,
                        assistant_payload=response_payload.model_dump(),
                        conversation_id=message.conversation_id,
                    )
                    response_payload.conversation_id = conversation.id
                    response_payload.message_id = assistant_message.id
                    response_payload.created_at = assistant_message.created_at
                except Exception as persist_err:
                    print(f"⚠️ [CHAT_HISTORY] Persist failed: {persist_err}")
            return response_payload

        # ── Preprocessing ─────────────────────────────────────────────────────
        print(f"📝 [ORIGINAL] {message.message}")
        normalized_message = text_preprocessor.preprocess(message.message)
        if normalized_message != message.message:
            print(f"✨ [NORMALIZED] {normalized_message}")

        # ── Compound query check ──────────────────────────────────────────────
        sub_queries = query_splitter.split(normalized_message)
        print(f"🔀 [SPLITTER] {len(sub_queries)} part(s): {[sq.detected_intent for sq in sub_queries]}")

        if len(sub_queries) > 1:
            # Multi-intent: process each sub-query independently
            parts: List[ChatResponseWithData] = []
            for sq in sub_queries:
                try:
                    part_resp = await _process_single_query(
                        normalized_text=sq.text,
                        student_id=message.student_id,
                        db=db,
                        chatbot_service=chatbot_service,
                    )
                except Exception as part_err:
                    print(f"⚠️ [COMPOUND] Sub-query error: {part_err}")
                    part_resp = ChatResponseWithData(
                        text=f"⚠️ Không thể xử lý phần này: {str(part_err)}",
                        intent=sq.detected_intent or "unknown",
                        confidence="low",
                        data=None,
                        sql=None,
                        sql_error=str(part_err),
                    )
                parts.append(part_resp)

            response_payload = _merge_responses(parts, sub_queries)
        else:
            # ── Single query (normal path) ────────────────────────────────────────
            response_payload = await _process_single_query(
                normalized_text=normalized_message,
                student_id=message.student_id,
                db=db,
                chatbot_service=chatbot_service,
            )

        if message.student_id:
            try:
                conversation, _, assistant_message = history_service.save_chat_turn(
                    student_pk=message.student_id,
                    user_content=message.message,
                    assistant_payload=response_payload.model_dump(),
                    conversation_id=message.conversation_id,
                )
                response_payload.conversation_id = conversation.id
                response_payload.message_id = assistant_message.id
                response_payload.created_at = assistant_message.created_at
            except Exception as persist_err:
                print(f"⚠️ [CHAT_HISTORY] Persist failed: {persist_err}")

        return response_payload

    except Exception as e:
        print(f"❌ [CHAT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý tin nhắn: {str(e)}")


def _generate_response_text(
    intent: str,
    confidence: str,
    classifier,
    data,
    sql_error: str = None
) -> str:
    """Generate response text based on intent, confidence and data"""

    if sql_error:
        return f"Xin lỗi, có lỗi khi truy vấn dữ liệu: {sql_error}"

    if confidence == "low":
        return "Mình chưa hiểu rõ câu hỏi của bạn, bạn vui lòng diễn giải lại được không?"

    if intent == "greeting":
        return "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?"

    if intent == "thanks":
        return "Rất vui được giúp đỡ bạn! Nếu có thắc mắc gì khác, hãy hỏi mình nhé 😊"

    if data is not None:
        if len(data) == 0:
            return "Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."
        if intent == "grade_view":
            return "Thông tin học vụ của bạn:"
        elif intent == "learned_subjects_view":
            return f"Đây là điểm các môn đã học của bạn (tìm thấy {len(data)} môn):"
        elif intent == "student_info":
            return "Đây là thông tin của bạn:"
        elif intent == "subject_info":
            return f"Thông tin về học phần (tìm thấy {len(data)} kết quả):"
        elif intent == "class_info":
            return f"Danh sách lớp học (tìm thấy {len(data)} lớp):"
        elif intent == "schedule_view":
            return f"Các môn/lớp bạn đã đăng ký (tìm thấy {len(data)} lớp):"

    intent_friendly_name = classifier.get_intent_friendly_name(intent)
    return f"Bạn định {intent_friendly_name} phải không?"


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


@router.get("/intents", response_model=IntentsResponse)
async def intents_endpoint():
    return await get_available_intents()


@router.post("/conversations", response_model=ChatConversationItem)
async def create_conversation(payload: ConversationCreateRequest, db: Session = Depends(get_db)):
    try:
        service = ChatHistoryService(db)
        conversation = service.create_conversation(
            student_pk=payload.student_id,
            title=payload.title,
        )
        return ChatConversationItem(
            id=conversation.id,
            student_pk=conversation.student_pk,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo conversation: {e}")


@router.get("/conversations", response_model=ChatConversationListResponse)
async def list_conversations(
    student_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        service = ChatHistoryService(db)
        result = service.list_conversations(
            student_pk=student_id,
            page=page,
            page_size=page_size,
        )
        return ChatConversationListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách conversation: {e}")


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def list_conversation_messages(
    conversation_id: int,
    student_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        service = ChatHistoryService(db)
        result = service.list_messages(
            student_pk=student_id,
            conversation_id=conversation_id,
            page=page,
            page_size=page_size,
        )
        return ConversationMessagesResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy tin nhắn conversation: {e}")


@router.patch("/conversations/{conversation_id}", response_model=ChatConversationItem)
async def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        service = ChatHistoryService(db)
        conversation = service.rename_conversation(
            student_pk=payload.student_id,
            conversation_id=conversation_id,
            title=payload.title,
        )
        return ChatConversationItem(
            id=conversation.id,
            student_pk=conversation.student_pk,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đổi tên conversation: {e}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    student_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    try:
        service = ChatHistoryService(db)
        service.delete_conversation(student_pk=student_id, conversation_id=conversation_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa conversation: {e}")


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
