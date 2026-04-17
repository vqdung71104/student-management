"""
Chatbot Routes - API endpoints cho chatbot with NL2SQL and Rule Engine
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService
from app.services.chatbot_service import ChatbotService
from app.services.text_preprocessor import get_text_preprocessor
from app.services.query_splitter import get_query_splitter, SubQuery
from app.services.chat_history_service import ChatHistoryService
from app.services.conversation_state import ConversationState, get_conversation_state_manager
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
from app.schemas.preference_schema import CompletePreference, PreferenceQuestion, PREFERENCE_QUESTIONS
from app.db.database import get_db
from app.models.student_model import Student
from app.utils.jwt_utils import get_current_student
from sqlalchemy import text
import uuid
import os

from app.agents.agent_orchestrator import AgentOrchestrator


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize TF-IDF intent classifier, NL2SQL service, and text preprocessor
intent_classifier = TfidfIntentClassifier()
nl2sql_service = NL2SQLService()
text_preprocessor = get_text_preprocessor()
query_splitter = get_query_splitter()
_agent_orchestrator: Optional[AgentOrchestrator] = None


def _get_agent_orchestrator() -> AgentOrchestrator:
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator


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
    "modify_schedule": "🛠️ Điều chỉnh thời khóa biểu",
    "student_info":                  "👤 Thông tin sinh viên",
}

_REGISTRATION_REMINDER_HTML = (
    "<div style='color:#d32f2f;font-size:20px;font-weight:800;line-height:1.4;'>"
    "⚠️ LƯU Ý QUAN TRỌNG: Sinh viên cần xem xét đăng ký học phần thực tập theo nhu cầu cá nhân; "
    "đồng thời kiểm tra đăng ký các học phần liên quan đến đồ án đúng tiến độ nhà trường và nhu cầu của mình."
    "</div>"
)


def _section_header(intent: str) -> str:
    return _SECTION_HEADERS.get(intent, f"ℹ️ {intent}")


def _prepend_registration_reminder(intent: str, text: str) -> str:
    """Prepend a prominent reminder for registration-related intents."""
    if intent not in {
        "class_registration_suggestion",
        "subject_registration_suggestion",
        "modify_schedule",
    }:
        return text

    if not text:
        return _REGISTRATION_REMINDER_HTML

    if "LƯU Ý QUAN TRỌNG" in text:
        return text

    return f"{_REGISTRATION_REMINDER_HTML}\n\n{text}"


def _sanitize_class_suggestion_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Keep response metadata compatible with Pydantic schema contract."""
    if not isinstance(metadata, dict):
        return metadata

    conversation = metadata.get("conversation")
    if not isinstance(conversation, dict):
        return metadata

    source_choice = conversation.get("source_choice")
    if source_choice is None or (isinstance(source_choice, str) and not source_choice.strip()):
        conversation["source_choice"] = "Học phần hệ thống gợi ý"
    elif not isinstance(source_choice, str):
        conversation["source_choice"] = str(source_choice)

    return metadata


def _normalize_subject_source_from_label(value: Optional[str]) -> str:
    if not value or not isinstance(value, str):
        return "suggested"
    lowered = value.strip().lower()
    if "đăng ký" in lowered and "hệ thống" not in lowered:
        return "registered"
    return "suggested"


def _restore_preferences_from_summary(summary: Optional[Dict[str, Any]]) -> CompletePreference:
    prefs = CompletePreference()
    if not isinstance(summary, dict):
        return prefs

    # Time preferences
    if summary.get("time_period") in ("morning", "afternoon"):
        prefs.time.time_period = summary.get("time_period")
    if isinstance(summary.get("avoid_time_periods"), list):
        prefs.time.avoid_time_periods = [
            period for period in summary.get("avoid_time_periods", []) if period in ("morning", "afternoon")
        ]
    prefs.time.prefer_early_start = bool(summary.get("prefer_early_start", False))
    prefs.time.prefer_late_start = bool(summary.get("prefer_late_start", False))
    prefs.time.avoid_early_start = bool(summary.get("avoid_early_start", False))
    prefs.time.avoid_late_end = bool(summary.get("avoid_late_end", False))
    prefs.time.is_not_important = bool(summary.get("time_is_not_important", False))
    prefs.time.has_answer = bool(
        prefs.time.time_period
        or prefs.time.avoid_time_periods
        or prefs.time.prefer_early_start
        or prefs.time.prefer_late_start
        or prefs.time.avoid_early_start
        or prefs.time.avoid_late_end
        or prefs.time.is_not_important
    )

    # Day preferences
    if isinstance(summary.get("prefer_days"), list):
        prefs.day.prefer_days = [str(day) for day in summary.get("prefer_days", [])]
    if isinstance(summary.get("avoid_days"), list):
        prefs.day.avoid_days = [str(day) for day in summary.get("avoid_days", [])]
    prefs.day.is_not_important = bool(summary.get("day_is_not_important", False))
    prefs.day.has_answer = bool(prefs.day.prefer_days or prefs.day.avoid_days or prefs.day.is_not_important)

    # Boolean preferences where "false" is ambiguous without full state snapshot.
    prefs.continuous.prefer_continuous = bool(summary.get("prefer_continuous", False))
    prefs.continuous.is_not_important = bool(summary.get("continuous_is_not_important", False))
    prefs.continuous.has_answer = bool(prefs.continuous.prefer_continuous or prefs.continuous.is_not_important)

    prefs.free_days.prefer_free_days = bool(summary.get("prefer_free_days", False))
    prefs.free_days.is_not_important = bool(summary.get("free_days_is_not_important", False))
    prefs.free_days.has_answer = bool(prefs.free_days.prefer_free_days or prefs.free_days.is_not_important)

    # Specific requirements
    if isinstance(summary.get("preferred_teachers"), list):
        prefs.specific.preferred_teachers = [str(item) for item in summary.get("preferred_teachers", [])]
    if isinstance(summary.get("specific_class_ids"), list):
        prefs.specific.specific_class_ids = [str(item) for item in summary.get("specific_class_ids", [])]
    if isinstance(summary.get("specific_subjects"), list):
        prefs.specific.specific_subjects = [str(item) for item in summary.get("specific_subjects", [])]
    if isinstance(summary.get("specific_times"), dict):
        prefs.specific.specific_times = summary.get("specific_times")
    prefs.specific.has_answer = bool(
        prefs.specific.preferred_teachers
        or prefs.specific.specific_class_ids
        or prefs.specific.specific_subjects
        or prefs.specific.specific_times
    )

    return prefs


def _build_assistant_payload_for_history(
    response_payload: ChatResponseWithData,
    conversation_id: int,
) -> Dict[str, Any]:
    assistant_payload = response_payload.model_dump()
    conv_manager = get_conversation_state_manager()
    state = conv_manager.get_state(conversation_id)

    if state and state.stage in ("collecting", "choose_subject_source"):
        assistant_payload["_conversation_state_snapshot"] = state.to_dict()

    return assistant_payload


def _hydrate_state_from_history_if_needed(
    history_service: ChatHistoryService,
    student_id: int,
    conversation_id: int,
) -> Optional[ConversationState]:
    conv_manager = get_conversation_state_manager()
    state = conv_manager.get_state(conversation_id)
    if state:
        return state

    latest_assistant = history_service.get_latest_assistant_message(
        student_pk=student_id,
        conversation_id=conversation_id,
    )
    if not latest_assistant:
        return None

    if latest_assistant.get("intent") != "class_registration_suggestion":
        return None

    data_json = latest_assistant.get("data_json")
    if not isinstance(data_json, dict):
        return None

    snapshot = data_json.get("conversation_state_snapshot")
    if isinstance(snapshot, dict):
        try:
            restored = ConversationState.from_dict(snapshot)
            restored.student_id = student_id
            restored.conversation_id = conversation_id
            conv_manager.save_state(restored)
            return restored
        except Exception as exc:
            print(f"⚠️ [HYDRATE] Failed to restore conversation snapshot {conversation_id}: {exc}")

    metadata = data_json.get("metadata")
    if not isinstance(metadata, dict):
        return None

    conversation_meta = metadata.get("conversation")
    if not isinstance(conversation_meta, dict):
        return None

    stage = str(conversation_meta.get("stage") or "").strip()
    next_step = str(conversation_meta.get("next_step") or "").strip()

    if stage == "completed" or next_step == "done":
        return None

    if stage not in {"collecting", "choose_subject_source"}:
        return None

    restored = ConversationState(
        student_id=student_id,
        session_id=f"rehydrate-{uuid.uuid4()}",
        conversation_id=conversation_id,
        intent="class_registration_suggestion",
    )
    restored.stage = stage

    preferences_meta = metadata.get("preferences") if isinstance(metadata.get("preferences"), dict) else {}
    restored.preferences = _restore_preferences_from_summary(preferences_meta.get("summary"))
    restored.supplemental_preference_keys = list(preferences_meta.get("auto_captured_keys", []) or [])
    restored.subject_source_choice = _normalize_subject_source_from_label(conversation_meta.get("source_choice"))
    restored.nlq_constraints = conversation_meta.get("nlq_constraints") if isinstance(conversation_meta.get("nlq_constraints"), dict) else None

    current_question = conversation_meta.get("current_question")
    if stage == "collecting" and isinstance(current_question, dict):
        question_key = current_question.get("key")
        if question_key in PREFERENCE_QUESTIONS:
            template = PREFERENCE_QUESTIONS[question_key]
            restored.current_question = PreferenceQuestion(
                key=template.key,
                question=current_question.get("question") or template.question,
                options=current_question.get("options") or template.options,
                type=current_question.get("type") or template.type,
                maps_to=template.maps_to,
            )

    conv_manager.save_state(restored)
    print(f"♻️ [HYDRATE] Restored class suggestion state for conversation {conversation_id} from history")
    return restored


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
    conversation_id: Optional[int],
    db: Session,
    chatbot_service: ChatbotService,
    forced_intent: Optional[str] = None,
) -> ChatResponseWithData:
    """Process one normalized sub-query and return ChatResponseWithData."""

    # ── Intent classification ─────────────────────────────────────────────────
    if forced_intent:
        intent = forced_intent
        confidence = "high"
    else:
        intent_result = await intent_classifier.classify_intent(normalized_text)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

    # Guardrail: source-choice answers ("đã đăng ký" / "hệ thống gợi ý") must stay in
    # class_registration_suggestion flow even if classifier drifts.
    if intent == "subject_registration_suggestion" and chatbot_service._parse_subject_source_choice(normalized_text):
        intent = "class_registration_suggestion"
        confidence = "high"

    # ── Rule-engine intents ───────────────────────────────────────────────────
    if intent in ("subject_registration_suggestion", "class_registration_suggestion", "modify_schedule") \
            and confidence in ("high", "medium"):
        if intent == "subject_registration_suggestion":
            result = await chatbot_service.process_subject_suggestion(
                student_id=student_id,
                question=normalized_text,
            )
        elif intent == "modify_schedule":
            result = await chatbot_service.process_modify_schedule(
                student_id=student_id,
                question=normalized_text,
            )
        else:
            result = await chatbot_service.process_class_suggestion(
                student_id=student_id,
                question=normalized_text,
                conversation_id=conversation_id,
            )

        result_data = result.get("data")
        if result_data is not None and not isinstance(result_data, list):
            if isinstance(result_data, dict):
                result_data = [result_data]
            else:
                result_data = [{"value": result_data}]

        display_text = _prepend_registration_reminder(result["intent"], result["text"])

        return ChatResponseWithData(
            text=display_text,
            intent=result["intent"],
            confidence=result["confidence"],
            data=result_data,
            metadata=_sanitize_class_suggestion_metadata(result.get("metadata")),
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
            has_structured_filters = any([
                bool(constraints.subject_codes),
                bool(constraints.subject_names),
                bool(constraints.class_ids),
                bool(constraints.class_names),
                bool(constraints.subject_ids),
                bool(constraints.days),
                bool(constraints.session),
                bool(constraints.day_session_constraints),
                bool(constraints.start_time_exact),
                bool(constraints.end_time_exact),
                bool(constraints.time_range),
                bool(constraints.time_from),
                bool(constraints.classroom_exact),
                bool(constraints.building_code),
                bool(constraints.room_code),
            ])

            if has_structured_filters:
                print(
                    f"🔍 [CLASS_INFO] codes={constraints.subject_codes} names={constraints.subject_names} "
                    f"class_ids={constraints.class_ids} class_names={constraints.class_names} "
                    f"subject_ids={constraints.subject_ids}"
                )
                svc = ClassQueryService(db)
                rows = svc.query(constraints)
                import datetime
                for r in rows:
                    if isinstance(r.get("study_time_start"), datetime.time):
                        r["study_time_start"] = r["study_time_start"].strftime("%H:%M")
                    if isinstance(r.get("study_time_end"), datetime.time):
                        r["study_time_end"] = r["study_time_end"].strftime("%H:%M")

                return ChatResponseWithData(
                    text=(
                        f"✅ Tìm thấy {len({str(r.get('class_id')) for r in rows if r.get('class_id') is not None}) or len(rows)} lớp học phù hợp."
                        if rows
                        else "Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."
                    ),
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
    sql_entities: Dict[str, Any] = {}

    nl2sql_intents = [
        "grade_view", "learned_subjects_view", "student_info", "subject_info",
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
            sql_entities = sql_result.get("entities") or {}

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

                if intent in ("subject_info", "class_info") and data and student_id:
                    data = _enrich_subject_or_class_data(
                        data=data,
                        student_id=student_id,
                        db=db,
                        entities=sql_entities,
                    )
        except Exception as e:
            sql_error = str(e)
            print(f"⚠️ SQL execution error: {e}")

    # ── Response text ─────────────────────────────────────────────────────────
    response_text = _generate_response_text(intent, confidence, intent_classifier, data, sql_error)
    if intent in ("subject_info", "class_info") and data:
        response_text = _append_learning_context_to_text(intent, response_text, data)

    return ChatResponseWithData(
        text=response_text,
        intent=intent,
        confidence=confidence,
        data=data,
        sql=sql_query,
        sql_error=sql_error,
    )


def _enrich_subject_or_class_data(
    data: List[Dict[str, Any]],
    student_id: int,
    db: Session,
    entities: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Annotate subject/class rows with student-specific learning context."""

    if not data:
        return data

    student_row = db.execute(
        text(
            """
            SELECT st.course_id, c.course_name
            FROM students st
            LEFT JOIN courses c ON c.id = st.course_id
            WHERE st.id = :student_id
            """
        ),
        {"student_id": student_id},
    ).mappings().first()

    if not student_row:
        return data

    course_pk = student_row.get("course_id")
    course_name = student_row.get("course_name")

    subject_codes: List[str] = []
    if entities.get("subject_ids"):
        subject_codes.extend([str(code) for code in entities["subject_ids"] if code])
    elif entities.get("subject_id"):
        subject_codes.append(str(entities["subject_id"]))

    if not subject_codes:
        subject_codes.extend([str(item.get("subject_id")) for item in data if item.get("subject_id")])

    subject_names = []
    if entities.get("subject_name"):
        subject_names.append(str(entities["subject_name"]))
    subject_names.extend([str(item.get("subject_name")) for item in data if item.get("subject_name")])

    if subject_names:
        for idx, name in enumerate(subject_names):
            row = db.execute(
                text(
                    """
                    SELECT subject_id
                    FROM subjects
                    WHERE subject_name = :subject_name
                    LIMIT 1
                    """
                ),
                {"subject_name": name},
            ).mappings().first()
            if row and row.get("subject_id"):
                subject_codes.append(str(row["subject_id"]))

    subject_codes = list(dict.fromkeys([code for code in subject_codes if code]))
    if not subject_codes:
        return data

    in_placeholders = ", ".join([f":subject_code_{i}" for i in range(len(subject_codes))])
    in_params = {f"subject_code_{i}": code for i, code in enumerate(subject_codes)}

    subject_meta_rows = db.execute(
        text(
            f"""
            SELECT
                sb.subject_id,
                sb.subject_name,
                CASE WHEN cs.id IS NULL THEN 0 ELSE 1 END AS in_program
            FROM subjects sb
            LEFT JOIN course_subjects cs
                ON cs.subject_id = sb.id
                AND cs.course_id = :course_pk
            WHERE sb.subject_id IN ({in_placeholders})
            """
        ),
        {"course_pk": course_pk, **in_params},
    ).mappings().all()

    learned_rows = db.execute(
        text(
            f"""
            SELECT
                sb.subject_id,
                ls.letter_grade,
                ls.semester
            FROM learned_subjects ls
            JOIN subjects sb ON sb.id = ls.subject_id
            WHERE ls.student_id = :student_id
              AND sb.subject_id IN ({in_placeholders})
            ORDER BY ls.semester DESC
            """
        ),
        {"student_id": student_id, **in_params},
    ).mappings().all()

    subject_meta_by_code = {row["subject_id"]: row for row in subject_meta_rows}
    subject_code_by_name = {row["subject_name"]: row["subject_id"] for row in subject_meta_rows}

    learned_by_code: Dict[str, List[Dict[str, Any]]] = {}
    for row in learned_rows:
        sid = row["subject_id"]
        learned_by_code.setdefault(sid, []).append(
            {
                "letter_grade": row["letter_grade"],
                "semester": row["semester"],
            }
        )

    enriched: List[Dict[str, Any]] = []
    for item in data:
        row = dict(item)
        sid = row.get("subject_id")
        if not sid and row.get("subject_name"):
            sid = subject_code_by_name.get(row["subject_name"])

        row["_student_course_name"] = course_name
        row["_student_course_pk"] = course_pk

        if not sid or sid not in subject_meta_by_code:
            row["_student_learning_status"] = "unknown"
            enriched.append(row)
            continue

        row["subject_id"] = sid
        meta = subject_meta_by_code[sid]
        in_program = bool(meta.get("in_program"))
        history = learned_by_code.get(sid, [])

        row["_in_student_program"] = in_program
        row["_student_grade_history"] = history

        if history:
            latest = history[0]
            row["_student_learning_status"] = "learned"
            row["_student_latest_grade"] = latest.get("letter_grade")
            row["_student_latest_semester"] = latest.get("semester")
            row["_student_context_message"] = (
                f"Bạn đã học học phần này ở kỳ {latest.get('semester')} và đạt điểm {latest.get('letter_grade')}."
            )
        elif in_program:
            row["_student_learning_status"] = "not_learned"
            row["_student_context_message"] = "Bạn chưa học học phần này."
        else:
            row["_student_learning_status"] = "out_of_program"
            row["_student_context_message"] = "Học phần này không nằm trong chương trình đào tạo của bạn."

        enriched.append(row)

    return enriched


def _append_learning_context_to_text(intent: str, base_text: str, data: List[Dict[str, Any]]) -> str:
    """Append high-level learning context for subject/class intents."""
    # For class rows, count logical classes (same class_id appears multiple sessions).
    rows_for_stats = data
    if intent == "class_info":
        by_class_code: Dict[str, Dict[str, Any]] = {}
        for row in data:
            class_code = row.get("class_id")
            key = str(class_code) if class_code is not None else str(row.get("id"))
            if key not in by_class_code:
                by_class_code[key] = row
        rows_for_stats = list(by_class_code.values())

    statuses = [row.get("_student_learning_status") for row in rows_for_stats if row.get("_student_learning_status")]
    if not statuses:
        return base_text

    learned = sum(1 for s in statuses if s == "learned")
    not_learned = sum(1 for s in statuses if s == "not_learned")
    out_program = sum(1 for s in statuses if s == "out_of_program")

    if intent == "subject_info":
        first_msg = data[0].get("_student_context_message")
        if first_msg:
            return f"{base_text}\n{first_msg}"
        return base_text

    notes: List[str] = []
    if out_program:
        notes.append(f"{out_program} lớp thuộc học phần không nằm trong chương trình đào tạo của bạn")
    if learned:
        notes.append(f"{learned} lớp thuộc học phần bạn đã học")
    if not_learned:
        notes.append(f"{not_learned} lớp thuộc học phần bạn chưa học")

    if notes:
        return f"{base_text}\nNgữ cảnh học tập: " + "; ".join(notes) + "."

    return base_text


# ─────────────────────────────────────────────────────────────────────────────
# Main chat endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponseWithData)
async def chat(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
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
        effective_student_id = current_student.id

        chatbot_service = ChatbotService(db)
        history_service = ChatHistoryService(db)
        conversation = history_service.get_or_create_conversation(
            student_pk=effective_student_id,
            conversation_id=message.conversation_id,
            first_message=message.message,
        )
        effective_conversation_id = conversation.id
        response_payload: ChatResponseWithData

        print(f"📝 [ORIGINAL] {message.message}")
        normalized_message = text_preprocessor.preprocess(message.message)
        if normalized_message != message.message:
            print(f"✨ [NORMALIZED] {normalized_message}")

        # ── Active conversation shortcut (preference collection in progress) ──
        state = _hydrate_state_from_history_if_needed(
            history_service=history_service,
            student_id=effective_student_id,
            conversation_id=effective_conversation_id,
        )

        if state and state.stage in ('collecting', 'choose_subject_source'):
            print(f"🔄 [ROUTE] Active conversation for conversation {effective_conversation_id}")
            result = await chatbot_service.process_class_suggestion(
                student_id=effective_student_id,
                question=normalized_message,
                conversation_id=effective_conversation_id,
            )
            response_payload = ChatResponseWithData(
                text=result["text"],
                intent=result["intent"],
                confidence=result["confidence"],
                data=result.get("data"),
                metadata=_sanitize_class_suggestion_metadata(result.get("metadata")),
                sql=None,
                sql_error=result.get("error"),
            )
            if effective_student_id:
                try:
                    conversation, _, assistant_message = history_service.save_chat_turn(
                        student_pk=effective_student_id,
                        user_content=message.message,
                        assistant_payload=_build_assistant_payload_for_history(
                            response_payload=response_payload,
                            conversation_id=effective_conversation_id,
                        ),
                        conversation_id=effective_conversation_id,
                    )
                    response_payload.conversation_id = conversation.id
                    response_payload.message_id = assistant_message.id
                    response_payload.created_at = assistant_message.created_at
                except Exception as persist_err:
                    print(f"⚠️ [CHAT_HISTORY] Persist failed: {persist_err}")
            return response_payload

        # Optional agent orchestration path (feature-flagged)
        if os.environ.get("AGENT_ENABLED", "false").lower() == "true":
            try:
                orchestrator = _get_agent_orchestrator()
                orchestration_result = await orchestrator.handle(
                    normalized_message,
                    student_id=effective_student_id,
                    conversation_id=effective_conversation_id,
                )
                # orchestration_result: {"raw": [...], "response": "..."}
                resp_text = orchestration_result.get('response') or ''
                raw = orchestration_result.get('raw')
                # derive intent/parts
                parts = []
                intent_label = 'unknown'
                confidence_label = 'medium'
                if isinstance(raw, list) and len(raw) > 0:
                    if len(raw) == 1:
                        intent_label = raw[0].get('intent', {}).get('intent') if isinstance(raw[0].get('intent'), dict) else raw[0].get('intent') or 'unknown'
                    else:
                        intent_label = 'compound'
                    for item in raw:
                        parts.append({
                            'intent': item.get('intent'),
                            'text': item.get('segment'),
                            'data': item.get('raw_result')
                        })

                response_payload = ChatResponseWithData(
                    text=resp_text,
                    intent=intent_label,
                    confidence=confidence_label,
                    data=None,
                    metadata=None,
                    sql=None,
                    sql_error=None,
                    is_compound=(intent_label == 'compound'),
                    parts=parts,
                )

                # persist history as before
                if effective_student_id:
                    try:
                        conversation, _, assistant_message = history_service.save_chat_turn(
                            student_pk=effective_student_id,
                            user_content=message.message,
                            assistant_payload=_build_assistant_payload_for_history(
                                response_payload=response_payload,
                                conversation_id=effective_conversation_id,
                            ),
                            conversation_id=effective_conversation_id,
                        )
                        response_payload.conversation_id = conversation.id
                        response_payload.message_id = assistant_message.id
                        response_payload.created_at = assistant_message.created_at
                    except Exception as persist_err:
                        print(f"⚠️ [CHAT_HISTORY] Persist failed: {persist_err}")

                return response_payload
            except Exception as ag_err:
                print(f"⚠️ [AGENT] Orchestration failed: {ag_err}")

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
                        student_id=effective_student_id,
                        conversation_id=effective_conversation_id,
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
                student_id=effective_student_id,
                conversation_id=effective_conversation_id,
                db=db,
                chatbot_service=chatbot_service,
            )

        if effective_student_id:
            try:
                conversation, _, assistant_message = history_service.save_chat_turn(
                    student_pk=effective_student_id,
                    user_content=message.message,
                    assistant_payload=_build_assistant_payload_for_history(
                        response_payload=response_payload,
                        conversation_id=effective_conversation_id,
                    ),
                    conversation_id=effective_conversation_id,
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

    def _logical_class_count(rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        class_keys = set()
        for row in rows:
            if row.get("class_id") is not None:
                class_keys.add(str(row.get("class_id")))
            elif row.get("id") is not None:
                class_keys.add(f"id:{row.get('id')}")
        return len(class_keys) if class_keys else len(rows)

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
            return "Đây là thông tin sinh viên của bạn (bao gồm chương trình đào tạo và GPA theo từng kỳ):"
        elif intent == "subject_info":
            return f"Thông tin về học phần (tìm thấy {len(data)} kết quả):"
        elif intent == "class_info":
            return f"Danh sách lớp học (tìm thấy {_logical_class_count(data)} lớp):"
        elif intent == "schedule_view":
            return f"Các môn/lớp bạn đã đăng ký (tìm thấy {_logical_class_count(data)} lớp):"

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


@router.post("/chat-stream")
async def chat_stream(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    Endpoint streaming tin nhắn từ user với real-time status updates
    
    Trả về Server-Sent Events stream với nhiều StreamChunk:
    - "status" chunks: cập nhật giai đoạn xử lý
    - "data" chunks: dữ liệu một phần đã lấy được
    - "done" chunk: phản hồi hoàn chỉnh
    - "error" chunk: lỗi xảy ra
    """
    from fastapi.responses import StreamingResponse
    from app.schemas.chatbot_schema import StreamChunk
    import json
    
    async def event_generator():
        def _emit(chunk: StreamChunk):
            payload = chunk.model_dump(exclude_none=True, mode="json")
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            effective_student_id = current_student.id
            chatbot_service = ChatbotService(db)
            history_service = ChatHistoryService(db)
            conversation = history_service.get_or_create_conversation(
                student_pk=effective_student_id,
                conversation_id=message.conversation_id,
                first_message=message.message,
            )
            effective_conversation_id = conversation.id

            print(f"📝 [STREAM] {message.message}")
            yield _emit(StreamChunk(type="status", stage="preprocessing", message="Đang chuẩn hóa câu hỏi..."))
            normalized_message = text_preprocessor.preprocess(message.message)
            if normalized_message != message.message:
                print(f"✨ [STREAM] {normalized_message}")

            state = _hydrate_state_from_history_if_needed(
                history_service=history_service,
                student_id=effective_student_id,
                conversation_id=effective_conversation_id,
            )

            response_payload: ChatResponseWithData

            # Keep identical behavior with /chat for active preference collection sessions.
            if state and state.stage in ('collecting', 'choose_subject_source'):
                yield _emit(StreamChunk(type="status", stage="classification", message="Đang tiếp tục hội thoại trước đó..."))

                result = await chatbot_service.process_class_suggestion(
                    student_id=effective_student_id,
                    question=normalized_message,
                    conversation_id=effective_conversation_id,
                )
                response_payload = ChatResponseWithData(
                    text=result["text"],
                    intent=result["intent"],
                    confidence=result["confidence"],
                    data=result.get("data"),
                    metadata=_sanitize_class_suggestion_metadata(result.get("metadata")),
                    sql=None,
                    sql_error=result.get("error"),
                )
            else:
                yield _emit(StreamChunk(type="status", stage="classification", message="Đang phân loại ý định câu hỏi..."))

                sub_queries = query_splitter.split(normalized_message)
                print(f"🔀 [STREAM][SPLITTER] {len(sub_queries)} part(s): {[sq.detected_intent for sq in sub_queries]}")

                if len(sub_queries) > 1:
                    yield _emit(StreamChunk(type="status", stage="query", message="Phát hiện câu hỏi nhiều phần, đang xử lý từng phần..."))
                    parts: List[ChatResponseWithData] = []

                    for idx, sq in enumerate(sub_queries):
                        yield _emit(
                            StreamChunk(
                                type="status",
                                stage="query",
                                message=f"Đang xử lý phần {idx + 1}/{len(sub_queries)}...",
                            )
                        )
                        try:
                            part_resp = await _process_single_query(
                                normalized_text=sq.text,
                                student_id=effective_student_id,
                                conversation_id=effective_conversation_id,
                                db=db,
                                chatbot_service=chatbot_service,
                            )
                        except Exception as part_err:
                            print(f"⚠️ [STREAM][COMPOUND] Sub-query error: {part_err}")
                            part_resp = ChatResponseWithData(
                                text=f"⚠️ Không thể xử lý phần này: {str(part_err)}",
                                intent=sq.detected_intent or "unknown",
                                confidence="low",
                                data=None,
                                sql=None,
                                sql_error=str(part_err),
                            )

                        if part_resp.data:
                            preview = part_resp.data[:5]
                            yield _emit(
                                StreamChunk(
                                    type="data",
                                    stage="query",
                                    message=f"Phần {idx + 1}: đã lấy {len(part_resp.data)} bản ghi",
                                    partial_data=preview,
                                    data_count=len(part_resp.data),
                                    total_count=len(part_resp.data),
                                )
                            )
                        parts.append(part_resp)

                    response_payload = _merge_responses(parts, sub_queries)
                else:
                    # If agent orchestration is enabled, use orchestrator for single-query path as well
                    if os.environ.get("AGENT_ENABLED", "false").lower() == "true":
                        yield _emit(StreamChunk(type="status", stage="query", message="Chuyển sang agent orchestration..."))
                        try:
                            orchestrator = _get_agent_orchestrator()
                            orchestration_result = await orchestrator.handle(
                                normalized_message,
                                student_id=effective_student_id,
                                conversation_id=effective_conversation_id,
                            )
                            resp_text = orchestration_result.get('response') or ''
                            raw = orchestration_result.get('raw')
                            parts = []
                            intent_label = 'unknown'
                            confidence_label = 'medium'
                            if isinstance(raw, list) and len(raw) > 0:
                                if len(raw) == 1:
                                    intent_label = raw[0].get('intent', {}).get('intent') if isinstance(raw[0].get('intent'), dict) else raw[0].get('intent') or 'unknown'
                                else:
                                    intent_label = 'compound'
                                for item in raw:
                                    parts.append({
                                        'intent': item.get('intent'),
                                        'text': item.get('segment'),
                                        'data': item.get('raw_result')
                                    })

                            response_payload = ChatResponseWithData(
                                text=resp_text,
                                intent=intent_label,
                                confidence=confidence_label,
                                data=None,
                                metadata=None,
                                sql=None,
                                sql_error=None,
                                is_compound=(intent_label == 'compound'),
                                parts=parts,
                            )
                        except Exception as ag_err:
                            print(f"⚠️ [STREAM][AGENT] Orchestration failed: {ag_err}")
                            response_payload = await _process_single_query(
                                normalized_text=normalized_message,
                                student_id=effective_student_id,
                                conversation_id=effective_conversation_id,
                                db=db,
                                chatbot_service=chatbot_service,
                            )
                    else:
                        yield _emit(StreamChunk(type="status", stage="query", message="Đang truy vấn dữ liệu..."))
                        response_payload = await _process_single_query(
                            normalized_text=normalized_message,
                            student_id=effective_student_id,
                            conversation_id=effective_conversation_id,
                            db=db,
                            chatbot_service=chatbot_service,
                        )
                    if response_payload.data:
                        preview = response_payload.data[:10]
                        yield _emit(
                            StreamChunk(
                                type="data",
                                stage="query",
                                message=f"Đã lấy {len(response_payload.data)} bản ghi",
                                partial_data=preview,
                                data_count=len(response_payload.data),
                                total_count=len(response_payload.data),
                            )
                        )

            if effective_student_id:
                try:
                    conversation, _, assistant_message = history_service.save_chat_turn(
                        student_pk=effective_student_id,
                        user_content=message.message,
                        assistant_payload=_build_assistant_payload_for_history(
                            response_payload=response_payload,
                            conversation_id=effective_conversation_id,
                        ),
                        conversation_id=effective_conversation_id,
                    )
                    response_payload.conversation_id = conversation.id
                    response_payload.message_id = assistant_message.id
                    response_payload.created_at = assistant_message.created_at
                except Exception as persist_err:
                    print(f"⚠️ [STREAM][CHAT_HISTORY] Persist failed: {persist_err}")

            yield _emit(
                StreamChunk(
                    type="done",
                    stage="complete",
                    text=response_payload.text,
                    intent=response_payload.intent,
                    confidence=response_payload.confidence,
                    data=response_payload.data,
                    metadata=response_payload.metadata,
                    is_compound=response_payload.is_compound,
                    parts=response_payload.parts,
                    conversation_id=response_payload.conversation_id,
                    message_id=response_payload.message_id,
                )
            )

        except Exception as e:
            print(f"❌ [STREAM] Error: {str(e)}")
            import traceback
            traceback.print_exc()

            error_chunk = StreamChunk(
                type="error",
                message="Có lỗi xảy ra khi xử lý câu hỏi",
                error_code="processing_error",
                error_detail=str(e),
            )
            yield _emit(error_chunk)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.get("/intents", response_model=IntentsResponse)
async def intents_endpoint():
    return await get_available_intents()


@router.post("/conversations", response_model=ChatConversationItem)
async def create_conversation(
    payload: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    try:
        service = ChatHistoryService(db)
        conversation = service.create_conversation(
            student_pk=current_student.id,
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
    current_student: Student = Depends(get_current_student),
):
    try:
        service = ChatHistoryService(db)
        result = service.list_conversations(
            student_pk=current_student.id,
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
    current_student: Student = Depends(get_current_student),
):
    try:
        service = ChatHistoryService(db)
        result = service.list_messages(
            student_pk=current_student.id,
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
    current_student: Student = Depends(get_current_student),
):
    try:
        service = ChatHistoryService(db)
        conversation = service.rename_conversation(
            student_pk=current_student.id,
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
    current_student: Student = Depends(get_current_student),
):
    try:
        service = ChatHistoryService(db)
        service.delete_conversation(student_pk=current_student.id, conversation_id=conversation_id)
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
