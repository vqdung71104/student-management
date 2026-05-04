"""
graph_nodes.py - Pure node functions for the LangGraph chatbot pipeline.
The LLM is used only for reasoning tasks such as split/route.
Formatting and filtering are rule-based for speed.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import unicodedata
from html import escape
from typing import Any, Dict, List, Optional, Tuple

from app.agents.graph_state import AgentState
from app.agents.orchestration_metrics import get_orchestration_metrics
from app.agents.tools_registry import ToolsRegistry
from app.db.database import SessionLocal
from app.llm.llm_client import LLMClient
from app.services.chatbot_service import format_rule_based_response as _service_format_rule_based_response

try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None

try:
    from app.services.text_preprocessor import get_text_preprocessor
except ImportError:
    get_text_preprocessor = None


INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
TFIDF_RULE_CONF_THRESHOLD = float(os.environ.get("TFIDF_RULE_CONF_THRESHOLD", "0.8"))
SIMPLE_QUERY_WORD_LIMIT = int(os.environ.get("SIMPLE_QUERY_WORD_LIMIT", "20"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "96"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "20.0"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "48"))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2.0"))
LLM_REASONING_TIMEOUT = float(os.environ.get("LLM_REASONING_TIMEOUT", "5.0"))
TOOL_EXECUTION_TIMEOUT = float(os.environ.get("TOOL_EXECUTION_TIMEOUT", "10.0"))
GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "55.0"))

_TRIM_FIELDS = frozenset(
    {
        "_student_course_pk",
        "_in_student_program",
        "_student_learning_status",
        "_student_grade_history",
        "_student_latest_grade",
        "_student_latest_semester",
        "_student_course_name",
        "_student_context_message",
        "_intent_type",
        "_id",
        "_score",
        "_rank",
    }
)
_MAX_ITEMS_PER_LIST = 20

_CONSTRAINT_PREFIXES = (
    "không muốn",
    "tránh",
    "ngoại trừ",
    "không học",
    "thay vì",
)

_CONSTRAINT_KEYWORDS = frozenset(
    {
        "khong muon",
        "khong hoc",
        "ngoai tru",
        "tranh",
        "thay vi",
        "sau",
        "truoc",
    }
)

_GRADUATION_KEYWORDS = frozenset(
    {
        "tin chi con lai",
        "tin chi thieu",
        "hoan thanh chuong trinh",
        "chuong trinh dao tao",
        "tot nghiep",
        "bao nhieu tin chi",
    }
)

_SUBJECT_REGISTRATION_BIAS_KEYWORDS = frozenset(
    {
        "dang ky",
        "nen hoc",
        "tu van mon",
    }
)
_CLASS_REGISTRATION_BIAS_KEYWORDS = frozenset(
    {
        "dang ky lop",
        "nen hoc lop",
        "goi y lop",
        "lop nao phu hop",
        "thoi gian hoc",
        "thu hoc",
    }
)
_LEARNED_SUBJECT_KEYWORDS = frozenset(
    {
        "diem mon",
        "diem hoc phan",
        "ket qua mon",
        "ket qua hoc phan",
        "mon da hoc",
        "mon bi d",
        "mon bi f",
        "mon truot",
        "mon rot",
    }
)
_GRADE_SUMMARY_KEYWORDS = frozenset({"cpa", "gpa", "diem tong ket"})
_STUDENT_INFO_KEYWORDS = frozenset({"thong tin sinh vien", "ma sinh vien", "lop sinh hoat"})

_NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})
_SOCIAL_INTENTS = frozenset({"greeting", "thanks", "goodbye"})
_SOCIAL_RESPONSE_MAP = {
    "greeting": "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?",
    "thanks": "Rất vui được giúp đỡ bạn. Nếu cần thêm thông tin, bạn cứ hỏi tiếp.",
    "goodbye": "Tạm biệt bạn. Khi nào cần tra cứu thông tin sinh viên, mình luôn sẵn sàng hỗ trợ.",
}
_SOCIAL_INTENT_PATTERNS = {
    "greeting": frozenset({"xin chao", "chao ban", "hello", "hi", "hey", "chao chatbot", "chao em", "chao"}),
    "thanks": frozenset({"cam on", "thank you", "thanks", "cam on ban", "cam on nhieu"}),
    "goodbye": frozenset({"tam biet", "bye", "goodbye", "hen gap lai", "thoi nhe"}),
}
_RULE_INTENT_BIASES = (
    ("class_registration_suggestion", frozenset({"dang ky lop", "nen hoc lop", "goi y lop", "lop nao phu hop"}), 0.97),
    ("subject_registration_suggestion", frozenset({"dang ky", "nen hoc", "tu van mon"}), 0.96),
    ("graduation_progress", frozenset({"tien do", "tot nghiep", "tin chi thieu", "tin chi con lai"}), 0.96),
    ("learned_subjects_view", frozenset({"diem mon", "diem hoc phan", "ket qua mon"}), 0.97),
    ("grade_view", frozenset({"cpa", "gpa", "diem tong ket"}), 0.96),
    ("student_info", frozenset({"thong tin sinh vien", "ma sinh vien", "lop sinh hoat"}), 0.96),
)
_FAST_SPLIT_REGEX = re.compile(
    r"\s*(?:,|;)?\s*(?:sau đó|đồng thời|tiếp theo|rồi|và)\s+",
    re.IGNORECASE,
)
_FAST_SPLIT_CONNECTOR_REGEX = re.compile(
    r"(?:sau đó|đồng thời|tiếp theo|rồi|và)",
    re.IGNORECASE,
)
_CONSTRAINT_REGEX = re.compile(
    r"(?:tôi\s+)?(?:không\s+muốn|tránh|ngoại\s+trừ|không\s+học|thay\s+vì)[^,;\.]*",
    re.IGNORECASE,
)

_PREFERRED_SUBJECT_REGEX = re.compile(
    r"(?:toi\s+)?(?:muon\s+hoc|muon\s+dang\s+ky|uu\s+tien\s+hoc|uu\s+tien)\s+(?:mon|hoc\s+phan)\s+[^,;\.]*",
    re.IGNORECASE,
)

_llm_client: Optional[LLMClient] = None
_tools_registry: Optional[ToolsRegistry] = None
_tfidf_classifier = TfidfIntentClassifier() if TfidfIntentClassifier else None
_text_preprocessor = get_text_preprocessor() if get_text_preprocessor else None
_metrics = get_orchestration_metrics()


def _normalize_text(text: str) -> str:
    normalized = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return normalized.lower()


def _get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def _get_tools() -> ToolsRegistry:
    global _tools_registry
    if _tools_registry is None:
        _tools_registry = ToolsRegistry()
    return _tools_registry


def _normalize_tool_payload(query: str, student_id: Optional[int], conversation_id: Optional[int]) -> Dict[str, Any]:
    return {
        "query": query,
        "q": query,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "params": {},
    }


async def _call_rule_based_backend(
    intent: str,
    query: str,
    student_id: Optional[int],
    conversation_id: Optional[int],
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    from app.routes.chatbot_routes import _process_single_query
    from app.services.chatbot_service import ChatbotService

    db = SessionLocal()
    try:
        normalized_query = _text_preprocessor.preprocess(query) if _text_preprocessor else query
        chatbot_service = ChatbotService(db)
        result = await _process_single_query(
            normalized_text=normalized_query,
            student_id=student_id,
            conversation_id=conversation_id,
            db=db,
            chatbot_service=chatbot_service,
            forced_intent=intent,
        )

        result_data = result.data
        data_count = len(result_data) if isinstance(result_data, list) else (1 if result_data else 0)
        tool_extra: Dict[str, Any] = {}
        preformatted_text: Optional[str] = None
        if isinstance(result.metadata, dict):
            tool_extra = {k: v for k, v in result.metadata.items() if k not in ("node", "duration_ms", "intent")}
            preformatted_text = result.metadata.get("preformatted_text")

        response_data: Dict[str, Any] = {
            "text": result.text or "",
            "intent": result.intent or intent,
            "confidence": result.confidence or "medium",
            "data": result_data,
            "sql": result.sql,
            "sql_error": result.sql_error,
        }
        if preformatted_text:
            response_data["preformatted_text"] = preformatted_text
        for key in (
            "question_type",
            "question_options",
            "conversation_state",
            "is_preference_collecting",
            "requires_auth",
            "download_url",
            "excel_url",
            "xlsx_url",
            "export_url",
        ):
            if isinstance(result.metadata, dict) and key in result.metadata:
                response_data[key] = result.metadata.get(key)

        if intent == "subject_registration_suggestion" and constraints:
            constrained_payload = chatbot_service.apply_subject_suggestion_constraints(response_data, constraints)
            response_data = constrained_payload
            updated_meta = constrained_payload.get("metadata")
            if isinstance(updated_meta, dict):
                tool_extra.update(updated_meta)
            result_data = response_data.get("data")
            data_count = len(result_data) if isinstance(result_data, list) else (1 if result_data else 0)

        return {
            "status": "success",
            "data": response_data,
            "metadata": {
                "node": "node3_tool_executor",
                "intent": intent,
                "data_count": data_count,
                **tool_extra,
            },
            "error": None,
        }
    finally:
        db.close()


def _is_complex_query(text: str) -> bool:
    lower = _normalize_text(text)
    return any(kw in lower for kw in _CONSTRAINT_KEYWORDS)


def _word_count(text: str) -> int:
    return len([token for token in re.split(r"\s+", text.strip()) if token])


def _is_simple_single_query(text: str) -> bool:
    return _word_count(text) < SIMPLE_QUERY_WORD_LIMIT and not _FAST_SPLIT_CONNECTOR_REGEX.search(text)


def _detect_social_intent(text: str) -> Optional[str]:
    normalized = _normalize_text(text).strip(" ,;.!?")
    for intent, patterns in _SOCIAL_INTENT_PATTERNS.items():
        if normalized in patterns:
            return intent
    return None


def _strip_leading_social_clause(text: str) -> str:
    parts = [part.strip() for part in re.split(r"\s*[,;:.!?]\s*", text) if part.strip()]
    if len(parts) < 2:
        return text
    if _detect_social_intent(parts[0]) in _SOCIAL_INTENTS:
        stripped = " ".join(parts[1:]).strip()
        return stripped or text
    return text


def _sanitize_segments(segments: List[str]) -> List[str]:
    cleaned = [segment.strip() for segment in segments if isinstance(segment, str) and segment.strip()]
    if not cleaned:
        return []
    if len(cleaned) == 1:
        return [_strip_leading_social_clause(cleaned[0])]

    non_social_segments = [segment for segment in cleaned if _detect_social_intent(segment) not in _SOCIAL_INTENTS]
    return non_social_segments or cleaned


def _build_social_response(intent: str) -> Dict[str, Any]:
    text = _SOCIAL_RESPONSE_MAP.get(intent, "Mình luôn sẵn sàng hỗ trợ bạn.")
    return {
        "text": text,
        "data": None,
        "model_used": "rule_based_social",
        "raw_data": {"text": text, "intent": intent},
        "intent": intent,
        "confidence": 1.0,
    }


def _pick_rule_based_intent(clean_query: str) -> Optional[Tuple[str, float, str]]:
    normalized = _normalize_text(clean_query)

    social_intent = _detect_social_intent(clean_query)
    if social_intent:
        return social_intent, 1.0, "social"

    personal_info_intent = _pick_personal_info_intent(clean_query)
    if personal_info_intent:
        return personal_info_intent

    for intent, keywords, confidence in _RULE_INTENT_BIASES:
        if any(keyword in normalized for keyword in keywords):
            return intent, confidence, "keyword_bias"

    if any(keyword in normalized for keyword in _GRADUATION_KEYWORDS):
        return "graduation_progress", 0.95, "keyword"

    return None


def safe_json_parse(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start():])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return {}


def _trim_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _trim_data(v) for k, v in data.items() if k not in _TRIM_FIELDS}
    if isinstance(data, list):
        if len(data) > _MAX_ITEMS_PER_LIST:
            return _trim_data(data[:_MAX_ITEMS_PER_LIST])
        return [_trim_data(item) for item in data]
    return data


def _is_data_empty(data: Any) -> bool:
    if data is None:
        return True
    if isinstance(data, list) and len(data) == 0:
        return True
    if isinstance(data, dict):
        if data.get("sql_error"):
            return True
        if data.get("is_preference_collecting") is True:
            return False
        keys_check = [
            "data",
            "result",
            "text",
            "rows",
            "items",
            "remaining_subjects",
            "total_credits_remaining",
        ]
        for key in keys_check:
            if key in data and data[key] not in (None, [], ""):
                return False
        if not any(k in data for k in keys_check):
            return True
    if isinstance(data, str) and not data.strip():
        return True
    return False


def _extract_result_data(raw_result: Any) -> Any:
    if raw_result is None:
        return None
    if isinstance(raw_result, dict):
        if "status" in raw_result and "data" in raw_result:
            return _extract_result_data(raw_result["data"])
        if "segment" in raw_result or "raw_result" in raw_result:
            return _extract_result_data(raw_result.get("raw_result", raw_result))
        return raw_result
    if isinstance(raw_result, list):
        if len(raw_result) == 0:
            return None
        if len(raw_result) == 1:
            return _extract_result_data(raw_result[0])
        return [_extract_result_data(item) for item in raw_result]
    return raw_result


def _unwrap_tool_payload(raw_result: Any) -> Any:
    if isinstance(raw_result, dict) and "status" in raw_result and "data" in raw_result:
        if raw_result.get("status") == "success":
            return raw_result.get("data")
        return {
            "text": raw_result.get("error") or raw_result.get("error_detail") or "Không thể xử lý yêu cầu.",
            "status": "error",
        }
    return raw_result


def _format_time_text(value: Any) -> str:
    if value is None:
        return "N/A"
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%H:%M")
        except Exception:
            pass
    return str(value)


def _aggregate_class_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        class_code = str(row.get("class_id") or row.get("id") or "N/A")
        slot = (
            f"{row.get('study_date') or 'N/A'} "
            f"{_format_time_text(row.get('study_time_start'))}-{_format_time_text(row.get('study_time_end'))}"
        )
        group = grouped.get(class_code)
        if group is None:
            group = {
                "class_id": row.get("class_id") or row.get("id") or "N/A",
                "subject_id": row.get("subject_id") or row.get("subject_code") or "",
                "subject_name": row.get("subject_name") or "",
                "teacher_name": row.get("teacher_name") or "Chưa có GV",
                "classroom": row.get("classroom") or "TBA",
                "study_week": row.get("study_week") or [],
                "slots": [],
            }
            grouped[class_code] = group
        if slot not in group["slots"]:
            group["slots"].append(slot)
        if group["teacher_name"] in ("", "Chưa có GV", "TBA") and row.get("teacher_name"):
            group["teacher_name"] = row.get("teacher_name")
        if group["classroom"] in ("", "TBA") and row.get("classroom"):
            group["classroom"] = row.get("classroom")
    return list(grouped.values())


def _render_class_info_html(rows: List[Dict[str, Any]]) -> str:
    logical_rows = _aggregate_class_rows(rows)
    if not logical_rows:
        return "<p>Không tìm thấy lớp học phù hợp.</p>"

    body_rows: List[str] = []
    for idx, row in enumerate(logical_rows, start=1):
        subject_label = escape(str(row.get("subject_name") or row.get("subject_id") or "N/A"))
        schedule_html = "<br/>".join(escape(slot) for slot in row.get("slots", [])) or "N/A"
        body_rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td><strong>{escape(str(row.get('class_id', 'N/A')))}</strong></td>"
            f"<td>{subject_label}</td>"
            f"<td>{schedule_html}</td>"
            f"<td>{escape(str(row.get('classroom', 'TBA')))}</td>"
            f"<td>{escape(str(row.get('teacher_name', 'Chưa có GV')))}</td>"
            "</tr>"
        )

    return (
        f"<div><strong>Danh sách lớp học</strong> - tìm thấy {len(logical_rows)} lớp phù hợp.</div>"
        "<table border='1' cellspacing='0' cellpadding='6' style='border-collapse:collapse;width:100%;margin-top:8px;'>"
        "<thead>"
        "<tr>"
        "<th>STT</th><th>Mã lớp</th><th>Học phần</th><th>Lịch học</th><th>Phòng</th><th>Giảng viên</th>"
        "</tr>"
        "</thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


def format_rule_based_response(raw_result: Any, intent: Optional[str], segment: Optional[str] = None) -> str:
    return _service_format_rule_based_response(raw_result, intent, segment)
    payload = _unwrap_tool_payload(raw_result)
    extracted = _extract_result_data(payload)

    if isinstance(payload, dict) and payload.get("preformatted_text"):
        return str(payload.get("preformatted_text"))

    if isinstance(payload, dict) and payload.get("text") and intent == "subject_registration_suggestion":
        return str(payload.get("text"))

    if intent == "class_info":
        rows = []
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            rows = payload.get("data") or []
        elif isinstance(payload, list):
            rows = payload
        return _render_class_info_html(rows)

    if isinstance(payload, dict) and payload.get("text"):
        return str(payload.get("text"))

    if _is_data_empty(extracted):
        return "Rất tiếc, mình không tìm thấy thông tin phù hợp với yêu cầu của bạn."

    if isinstance(extracted, list):
        return f"<div>Tìm thấy {len(extracted)} kết quả cho yêu cầu này.</div>"

    if isinstance(extracted, dict):
        items = []
        for key, value in list(_trim_data(extracted).items())[:8]:
            if isinstance(value, (str, int, float, bool)) and value not in ("", None):
                items.append(f"<li><strong>{escape(str(key))}:</strong> {escape(str(value))}</li>")
        if items:
            return f"<ul>{''.join(items)}</ul>"

    return "Mình đã xử lý xong yêu cầu của bạn."


def _build_graduation_rows(payload: Any, raw: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload.get("data") or []

    metadata = raw.get("metadata") if isinstance(raw, dict) else None
    if metadata is None and isinstance(payload, dict):
        metadata = payload.get("metadata")
    summary = metadata.get("summary") if isinstance(metadata, dict) else None
    missing_subjects = summary.get("missing_subjects") if isinstance(summary, dict) else None
    rows: List[Dict[str, Any]] = []

    if not isinstance(missing_subjects, list):
        return rows

    for item in missing_subjects:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        rows.append(
            {
                "action": "Cáº§n há»c láº¡i ngay" if status == "failed" else "Cáº§n há»c",
                "status": status,
                "credits": item.get("credits"),
                "subject_id": item.get("subject_id"),
                "subject_name": item.get("subject_name"),
            }
        )
    return rows


def _extract_preserved_data(raw: Any, payload: Any, intent: Optional[str]) -> Any:
    if intent == "graduation_progress":
        rows = _build_graduation_rows(payload, raw)
        return rows if rows else None

    if isinstance(payload, dict) and payload.get("data") is not None:
        return payload.get("data")
    if isinstance(payload, list):
        return payload
    return None


def _build_formatted_response(raw: Any, intent: Optional[str], segment: Optional[str] = None) -> Dict[str, Any]:
    payload = _unwrap_tool_payload(raw)
    text = format_rule_based_response(raw, intent, segment)
    data = _extract_preserved_data(raw, payload, intent)
    metadata = raw.get("metadata") if isinstance(raw, dict) else None

    if isinstance(raw, dict) and raw.get("status") == "success" and isinstance(payload, dict):
        header = payload.get("text", "")
        details = payload.get("data")
        if isinstance(details, list) and details:
            if intent == "grade_view":
                first_item = details[0]
                data_str = (
                    f" CPA: {first_item.get('cpa')} | "
                    f"TÃ­n chá»‰ tÃ­ch lÅ©y: {first_item.get('total_learned_credits')}"
                )
                text = header if str(first_item.get("cpa")) in header else f"{header}\n- {data_str}"
            else:
                text = text or header

    service_text = _service_format_rule_based_response(raw, intent, segment)
    if service_text and str(service_text).strip():
        text = service_text

    if not text or not str(text).strip():
        text = "YÃªu cáº§u Ä‘Ã£ Ä‘Æ°á»£c xá»­ lÃ½ thÃ nh cÃ´ng."

    formatted: Dict[str, Any] = {
        "text": text,
        "data": data,
        "model_used": "rule_based_enhanced",
        "raw_data": raw,
    }
    if metadata is not None:
        formatted["metadata"] = metadata
    for source in (payload if isinstance(payload, dict) else None, metadata if isinstance(metadata, dict) else None):
        if not isinstance(source, dict):
            continue
        for key in (
            "question_type",
            "question_options",
            "conversation_state",
            "is_preference_collecting",
            "requires_auth",
            "rule_engine_used",
            "intent",
            "confidence",
            "file_url",
            "download_url",
            "excel_url",
            "xlsx_url",
            "export_url",
            "preformatted_text",
        ):
            if key in source and key not in formatted:
                formatted[key] = source.get(key)
    return formatted


def join_rule_based_segments(segment_texts: List[str]) -> str:
    cleaned = [text.strip() for text in segment_texts if isinstance(text, str) and text.strip()]
    return "<hr/>".join(cleaned) if cleaned else "Xin lỗi, mình không tìm thấy dữ liệu."


def _regex_split_segments(text: str) -> Tuple[List[str], bool, bool]:
    has_connector = bool(_FAST_SPLIT_CONNECTOR_REGEX.search(text))
    if not has_connector:
        return [text], False, False

    parts = [part.strip(" ,;") for part in _FAST_SPLIT_REGEX.split(text) if part.strip(" ,;")]
    uncertain = False
    if len(parts) < 2:
        uncertain = True
    if any(len(part.split()) < 2 for part in parts):
        uncertain = True
    if any(_CONSTRAINT_REGEX.match(part) for part in parts[1:]):
        uncertain = True
    return parts or [text], True, uncertain


def _strip_constraints(text: str) -> tuple[str, List[str]]:
    phrases = [match.group(0).strip() for match in _CONSTRAINT_REGEX.finditer(text)]
    clean = text
    for phrase in phrases:
        clean = clean.replace(phrase, "")
    clean = re.sub(r"[,;\s]{2,}", " ", clean)
    clean = re.sub(r"^[,;\s]+|[,;\s]+$", "", clean).strip()
    return clean if clean else text, phrases


def _extract_excluded_subjects(constraint_phrases: List[str]) -> List[str]:
    exclude_subjects: List[str] = []
    seen = set()
    for phrase in constraint_phrases:
        normalized = _normalize_text(phrase)
        normalized = re.sub(
            r"^(?:toi\s+)?(?:khong\s+muon|tranh|ngoai\s+tru|khong\s+hoc|thay\s+vi)\s*",
            "",
            normalized,
        ).strip(" ,.;")
        if not normalized:
            continue
        for part in re.split(r",|;|\s+va\s+|\s+hoac\s+", normalized):
            cleaned = re.sub(r"^(?:mon|hoc phan|lop)\s+", "", part).strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                exclude_subjects.append(cleaned)
    return exclude_subjects


def _extract_preferred_subjects(text: str) -> List[str]:
    preferred_subjects: List[str] = []
    seen = set()
    for phrase in _PREFERRED_SUBJECT_REGEX.findall(_normalize_text(text)):
        normalized = re.sub(
            r"^(?:toi\s+)?(?:muon\s+hoc|muon\s+dang\s+ky|uu\s+tien\s+hoc|uu\s+tien)\s+(?:mon|hoc\s+phan)\s*",
            "",
            phrase,
        ).strip(" ,.;")
        if not normalized:
            continue
        for part in re.split(r",|;|\s+va\s+|\s+hoac\s+", normalized):
            cleaned = re.sub(r"^(?:mon|hoc phan|lop)\s+", "", part).strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                preferred_subjects.append(cleaned)
    return preferred_subjects


def _should_force_class_info(clean_query: str) -> bool:
    lowered = _normalize_text(clean_query)
    return "lop" in lowered and not any(keyword in lowered for keyword in _CLASS_REGISTRATION_BIAS_KEYWORDS | _SUBJECT_REGISTRATION_BIAS_KEYWORDS)


def _should_force_subject_info(clean_query: str) -> bool:
    lowered = _normalize_text(clean_query)
    if "lop" in lowered:
        return False
    if any(keyword in lowered for keyword in _CLASS_REGISTRATION_BIAS_KEYWORDS | _SUBJECT_REGISTRATION_BIAS_KEYWORDS):
        return False
    return any(token in lowered for token in ("hoc phan", "mon ")) or bool(re.search(r"\b[a-z]{2,4}\d{3,4}[a-z]?\b", lowered))


def _contains_subject_reference(clean_query: str) -> bool:
    lowered = _normalize_text(clean_query)
    if bool(re.search(r"\b[a-z]{2,4}\d{3,4}[a-z]?\b", lowered)):
        return True
    if any(keyword in lowered for keyword in ("mon ", "hoc phan", "tieng nhat", "giai tich", "dai so")):
        return True
    return False


def _pick_personal_info_intent(clean_query: str) -> Optional[Tuple[str, float, str]]:
    normalized = _normalize_text(clean_query)

    if any(keyword in normalized for keyword in _CLASS_REGISTRATION_BIAS_KEYWORDS):
        return "class_registration_suggestion", 0.98, "keyword_bias"

    if any(keyword in normalized for keyword in _STUDENT_INFO_KEYWORDS):
        return "student_info", 0.97, "keyword_bias"

    if any(keyword in normalized for keyword in _LEARNED_SUBJECT_KEYWORDS):
        return "learned_subjects_view", 0.98, "keyword_bias"

    if "diem" in normalized and _contains_subject_reference(clean_query) and not any(keyword in normalized for keyword in _GRADE_SUMMARY_KEYWORDS):
        return "learned_subjects_view", 0.96, "keyword_bias"

    if any(keyword in normalized for keyword in _GRADE_SUMMARY_KEYWORDS):
        return "grade_view", 0.97, "keyword_bias"

    return None


def _should_use_agent(state: AgentState, intent: str, is_complex: bool) -> bool:
    segments = state.get("segments", []) or []
    is_single_segment = len(segments) <= 1
    if is_single_segment and not is_complex:
        return False
    return True


async def query_splitter_node(state: AgentState) -> Dict[str, Any]:
    text = state.get("user_text", "")
    if _is_simple_single_query(text):
        return {"segments": _sanitize_segments([text]), "node_trace": ["query_splitter_node"]}

    regex_segments, has_connector, uncertain = _regex_split_segments(text)
    if has_connector and len(regex_segments) >= 2 and not uncertain:
        print(f"[NODE1] fast_regex_split={len(regex_segments)}")
        return {"segments": _sanitize_segments(regex_segments), "node_trace": ["query_splitter_node"]}

    if has_connector:
        fallback_segments = regex_segments
    else:
        fallback_segments = [text]

    try:
        llm = _get_llm()

        res = await llm.split(
            text,
            timeout=NODE1_TIMEOUT,
            max_tokens=NODE1_SPLIT_MAX_TOKENS,
            temperature=0.0,
        )
        segments = _sanitize_segments(res.get("segments", []) or fallback_segments)
        print(f"[NODE1] openai_split={len(segments)}")
        return {"segments": segments, "node_trace": ["query_splitter_node"]}
    except Exception as exc:
        print(f"[NODE1] splitter_fallback error={exc}")
        return {"segments": _sanitize_segments(fallback_segments or [text]), "node_trace": ["query_splitter_node"]}


async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    seg = state.get("segments")[state.get("current_segment_index", 0)]
    seg = _strip_leading_social_clause(seg)
    clean_query, constraint_phrases = _strip_constraints(seg)
    constraints: Dict[str, Any] = {
        "constraint_phrases": constraint_phrases,
        "exclude_subjects": _extract_excluded_subjects(constraint_phrases) if constraint_phrases else [],
        "preferred_subjects": _extract_preferred_subjects(seg),
        "forbidden_time_slots": [],
        "forbidden_times": [],
        "semester": None,
        "days": [],
    }
    is_complex = bool(constraint_phrases) or _is_complex_query(seg)
    lower_clean_query = _normalize_text(clean_query)
    is_single_segment = len(state.get("segments", []) or []) <= 1

    forced_intent = _pick_rule_based_intent(clean_query)
    if forced_intent:
        intent, confidence, source = forced_intent
        return {
            "intent": intent,
            "confidence": confidence,
            "intent_source": source,
            "is_complex": is_complex,
            "needs_agent": False,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if constraint_phrases and any(keyword in lower_clean_query for keyword in _SUBJECT_REGISTRATION_BIAS_KEYWORDS):
        return {
            "intent": "subject_registration_suggestion",
            "confidence": 0.95,
            "intent_source": "keyword_bias",
            "is_complex": True,
            "needs_agent": False,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if constraints.get("preferred_subjects") and any(keyword in lower_clean_query for keyword in ("muon hoc", "muon dang ky", "uu tien")):
        return {
            "intent": "subject_registration_suggestion",
            "confidence": 0.95,
            "intent_source": "constraint_bias",
            "is_complex": True,
            "needs_agent": True,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if any(keyword in lower_clean_query for keyword in _CLASS_REGISTRATION_BIAS_KEYWORDS):
        return {
            "intent": "class_registration_suggestion",
            "confidence": 0.97,
            "intent_source": "keyword_bias",
            "is_complex": is_complex,
            "needs_agent": False,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if any(keyword in lower_clean_query for keyword in _GRADUATION_KEYWORDS):
        needs_agent = _should_use_agent(state, "graduation_progress", is_complex)
        return {
            "intent": "graduation_progress",
            "confidence": 0.95,
            "intent_source": "keyword",
            "is_complex": is_complex,
            "needs_agent": needs_agent,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if _should_force_class_info(clean_query):
        return {
            "intent": "class_info",
            "confidence": 0.96,
            "intent_source": "keyword",
            "is_complex": is_complex,
            "needs_agent": False,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if _should_force_subject_info(clean_query):
        return {
            "intent": "subject_info",
            "confidence": 0.95,
            "intent_source": "keyword",
            "is_complex": is_complex,
            "needs_agent": False,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    has_reg = "dang ky" in lower_clean_query or "register" in lower_clean_query
    if has_reg and is_complex:
        return {
            "intent": "subject_registration_suggestion",
            "confidence": 0.95,
            "intent_source": "bias",
            "is_complex": True,
            "needs_agent": True,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    intent = "unknown"
    confidence = 0.0

    if _tfidf_classifier and clean_query:
        try:
            tfidf_res = await _tfidf_classifier.classify_intent(clean_query)
            intent = tfidf_res.get("intent", "unknown")
            confidence = float(tfidf_res.get("confidence_score", 0.0))
            if confidence >= INTENT_CONF_THRESHOLD:
                needs_agent = False if is_single_segment and confidence >= TFIDF_RULE_CONF_THRESHOLD else _should_use_agent(state, intent, is_complex)
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "intent_source": "tfidf",
                    "is_complex": is_complex,
                    "needs_agent": needs_agent,
                    "constraints": constraints,
                    "clean_query": clean_query,
                    "node_trace": ["intent_router_node"],
                }
        except Exception as exc:
            print(f"[NODE2] TF-IDF failed: {exc}")

    should_call_llm = bool(clean_query) and (is_complex or intent in ("unknown", "out_of_scope") or confidence < INTENT_CONF_THRESHOLD)
    if should_call_llm:
        try:
            llm = _get_llm()

            llm_res = await llm.classify(
                clean_query,
                timeout=NODE2_TIMEOUT,
                max_tokens=NODE2_CLASSIFY_MAX_TOKENS,
                temperature=0.0,
            )
            intent = llm_res.get("intent", "unknown")
            confidence = float(llm_res.get("confidence", 0.0))
            needs_agent = _should_use_agent(state, intent, is_complex)
            return {
                "intent": intent,
                "confidence": confidence,
                "intent_source": "openai",
                "is_complex": is_complex,
                "needs_agent": needs_agent,
                "constraints": constraints,
                "clean_query": clean_query,
                "node_trace": ["intent_router_node"],
            }
        except Exception as exc:
            print(f"[NODE2] OpenAI classify failed: {exc}")

    return {
        "intent": intent,
        "confidence": confidence,
        "intent_source": "fallback",
        "is_complex": is_complex,
        "needs_agent": False,
        "constraints": constraints,
        "clean_query": clean_query,
        "reasoning_fallback": True,
        "node_trace": ["intent_router_node"],
    }


def constraint_parser_node(state: AgentState) -> Dict[str, Any]:
    constraints = state.get("constraints", {})
    phrases = constraints.get("constraint_phrases") or []
    if phrases:
        constraints["exclude_subjects"] = _extract_excluded_subjects(phrases)
    return {"constraints": constraints, "node_trace": ["constraint_parser_node"]}


async def tool_executor_node(state: AgentState) -> Dict[str, Any]:
    seg = state.get("segments", [""])[state.get("current_segment_index", 0)]
    intent = state.get("intent", "unknown")
    raw_data = {"message": "No tool mapped", "items": []}
    needs_agent_filter = (intent in _NODE3B_INTENTS) or bool(
        state.get("constraints", {}).get("exclude_subjects")
    )
    query = state.get("clean_query", seg)
    student_id = state.get("student_id")
    conversation_id = state.get("conversation_id")

    if intent in _SOCIAL_INTENTS:
        return {
            "raw_data": {"text": _SOCIAL_RESPONSE_MAP.get(intent), "intent": intent},
            "needs_agent_filter": False,
            "node_trace": ["tool_executor_node"],
        }

    if intent not in ("unknown", None, ""):
        try:
            raw_data = await asyncio.wait_for(
                _call_rule_based_backend(
                    intent=intent,
                    query=query,
                    student_id=student_id,
                    conversation_id=conversation_id,
                    constraints=state.get("constraints"),
                ),
                timeout=TOOL_EXECUTION_TIMEOUT,
            )
        except Exception as exc:
            try:
                tools = _get_tools()
                raw_data = await asyncio.wait_for(
                    tools.call(intent, _normalize_tool_payload(query, student_id, conversation_id)),
                    timeout=TOOL_EXECUTION_TIMEOUT,
                )
            except Exception as fallback_exc:
                raw_data = {"status": "error", "error": str(fallback_exc or exc)}

    return {
        "raw_data": raw_data,
        "needs_agent_filter": needs_agent_filter,
        "node_trace": ["tool_executor_node"],
    }


def agent_filter_node(state: AgentState) -> Dict[str, Any]:
    raw_data = state.get("raw_data")
    constraints = state.get("constraints", {})
    excluded = constraints.get("exclude_subjects", [])
    preferred = constraints.get("preferred_subjects", [])
    filtered_data = raw_data

    payload = _unwrap_tool_payload(raw_data)
    rows = None
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload.get("data")

    if excluded and rows is not None:
        filtered_rows = [
            item
            for item in rows
            if not any(exc in _normalize_text(str(item.get("subject_name", ""))) for exc in excluded)
        ]
        rows = filtered_rows

    if preferred and rows is not None:
        preferred_rows = [
            item for item in rows
            if any(term in _normalize_text(str(item.get("subject_name", ""))) or term in _normalize_text(str(item.get("subject_id", ""))) for term in preferred)
        ]
        remaining_rows = [item for item in rows if item not in preferred_rows]
        rows = preferred_rows + remaining_rows

    if rows is not None:
        payload["data"] = rows
        if isinstance(raw_data, dict) and "status" in raw_data and "data" in raw_data:
            raw_data["data"] = payload
            filtered_data = raw_data
        else:
            filtered_data = payload

    return {"filtered_data": filtered_data, "node_trace": ["agent_filter_node"]}


def _legacy_response_formatter_node(state: AgentState) -> Dict[str, Any]:
    raw = state.get("filtered_data") or state.get("raw_data")
    idx = state.get("current_segment_index", 0)
    segments = state.get("segments", [""])
    seg = segments[idx] if idx < len(segments) else ""
    intent = state.get("intent", "unknown")
    
    # 1. Thử lấy text theo rule-based formatter
    text = format_rule_based_response(raw, intent, seg)
    
    # 2. KIỂM TRA NÂNG CAO: Nếu text chỉ là câu dẫn, hãy nối thêm dữ liệu số liệu
    if isinstance(raw, dict) and raw.get("status") == "success":
        payload = raw.get("data", {})
        if isinstance(payload, dict):
            # Lấy câu dẫn
            header = payload.get("text", "")
            
            # Lấy dữ liệu chi tiết (như cpa, credits)
            details = payload.get("data")
            if details and isinstance(details, list) and len(details) > 0:
                # Nếu là grade_view, tạo chuỗi hiển thị số liệu
                if intent == "grade_view":
                    d = details[0]
                    data_str = f" CPA: {d.get('cpa')} | Tín chỉ tích lũy: {d.get('total_learned_credits')}"
                    # Nối vào câu dẫn nếu câu dẫn chưa chứa số liệu
                    if str(d.get('cpa')) not in header:
                        text = f"{header}\n- {data_str}"
                    else:
                        text = header
                else:
                    # Cho các intent khác, dùng lại logic cũ hoặc để header
                    text = text or header

    # 3. Dự phòng cuối cùng
    if not text or text.strip() == "":
        text = "Yêu cầu đã được xử lý thành công."

    return {
        "final_response": text,
        "formatted_result": {
            "text": text,
            "model_used": "rule_based_enhanced",
        },
        "node_trace": ["response_formatter_node"],
    }


def response_formatter_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "unknown")
    segments = state.get("segments", [])
    if intent in _SOCIAL_INTENTS and len(segments) <= 1:
        formatted = _build_social_response(intent)
        return {
            "final_response": formatted["text"],
            "formatted_result": formatted,
            "node_trace": ["response_formatter_node"],
        }

    raw = state.get("filtered_data") or state.get("raw_data")
    idx = state.get("current_segment_index", 0)
    segments = segments or [""]
    seg = segments[idx] if idx < len(segments) else ""
    formatted = _build_formatted_response(raw, intent, seg)

    return {
        "final_response": formatted["text"],
        "formatted_result": formatted,
        "node_trace": ["response_formatter_node"],
    }


def _accumulate_and_route_node(state: AgentState) -> Dict[str, Any]:
    idx = state.get("current_segment_index", 0)
    final_raw = state.get("filtered_data") or state.get("raw_data")
    current_formatted = state.get("final_response", "")
    seg_result = {
        "segment": state.get("segments")[idx],
        "intent": {"intent": state.get("intent"), "confidence": state.get("confidence")},
        "raw_result": final_raw,
        "formatted_text": current_formatted,
        "formatted_result": state.get("formatted_result"),
        "route": "agent" if state.get("needs_agent") else "rule_based",
    }
    return {
        "segment_results": [seg_result],
        "current_segment_index": idx + 1,
        "final_response": None,
        "raw_data": None,
        "filtered_data": None,
        "node_trace": ["_accumulate_and_route_node"],
    }


def synthesize_formatter_node(state: AgentState) -> Dict[str, Any]:
    results = state.get("segment_results", [])
    if not results:
        return {"final_response": "Xin lỗi, mình không tìm thấy dữ liệu."}
    if len(results) == 1:
        return {"final_response": results[0].get("formatted_text")}
    final_output = join_rule_based_segments([result.get("formatted_text", "") for result in results])
    return {
        "synthesized_response": final_output,
        "final_response": final_output,
        "node_trace": ["synthesize_formatter_node"],
    }


def join_rule_based_segments(segment_texts: List[str]) -> str:
    cleaned = [text.strip() for text in segment_texts if isinstance(text, str) and text.strip()]
    return "<hr/>".join(cleaned) if cleaned else "Xin loi, minh khong tim thay du lieu."


def _segment_result_text(result: Dict[str, Any]) -> str:
    formatted_result = result.get("formatted_result") or {}
    raw_result = result.get("raw_result") or {}
    return (
        result.get("formatted_text")
        or formatted_result.get("text")
        or _service_format_rule_based_response(
            raw_result,
            ((result.get("intent") or {}).get("intent")) or "unknown",
            result.get("segment"),
        )
        or ""
    )


def synthesize_formatter_node(state: AgentState) -> Dict[str, Any]:
    results = state.get("segment_results", [])
    if not results:
        return {"final_response": "Xin loi, minh khong tim thay du lieu."}

    combined_parts = [_segment_result_text(result) for result in results]
    final_output = join_rule_based_segments(combined_parts)
    return {
        "synthesized_response": final_output,
        "final_response": final_output,
        "node_trace": ["synthesize_formatter_node"],
    }


def rule_based_fallback_node(state: AgentState) -> Dict[str, Any]:
    return {
        "used_fallback": True,
        "raw_data": {
            "text": "Mình chưa phân tích kịp yêu cầu trong thời gian cho phép. Bạn vui lòng thử lại hoặc chia nhỏ câu hỏi giúp mình.",
        },
        "node_trace": ["rule_based_fallback_node"],
    }
