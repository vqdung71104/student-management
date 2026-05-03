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
from app.llm.llm_client import LLMClient

try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None


INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "96"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "3.0"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "48"))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2.0"))
LLM_REASONING_TIMEOUT = float(os.environ.get("LLM_REASONING_TIMEOUT", "5.0"))
TOOL_EXECUTION_TIMEOUT = float(os.environ.get("TOOL_EXECUTION_TIMEOUT", "10.0"))
GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))

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

_NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})
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

_llm_client: Optional[LLMClient] = None
_tools_registry: Optional[ToolsRegistry] = None
_tfidf_classifier = TfidfIntentClassifier() if TfidfIntentClassifier else None
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


def _is_complex_query(text: str) -> bool:
    lower = _normalize_text(text)
    return any(kw in lower for kw in _CONSTRAINT_KEYWORDS)


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


async def query_splitter_node(state: AgentState) -> Dict[str, Any]:
    text = state.get("user_text", "")
    regex_segments, has_connector, uncertain = _regex_split_segments(text)
    if has_connector and len(regex_segments) >= 2 and not uncertain:
        print(f"[NODE1] fast_regex_split={len(regex_segments)}")
        return {"segments": regex_segments, "node_trace": ["query_splitter_node"]}

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
        segments = res.get("segments", []) or fallback_segments
        print(f"[NODE1] openai_split={len(segments)}")
        return {"segments": segments, "node_trace": ["query_splitter_node"]}
    except Exception as exc:
        print(f"[NODE1] splitter_fallback error={exc}")
        return {"segments": fallback_segments or [text], "node_trace": ["query_splitter_node"]}


async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    seg = state.get("segments")[state.get("current_segment_index", 0)]
    clean_query, constraint_phrases = _strip_constraints(seg)
    constraints: Dict[str, Any] = {
        "constraint_phrases": constraint_phrases,
        "exclude_subjects": [],
        "forbidden_time_slots": [],
        "forbidden_times": [],
        "semester": None,
        "days": [],
    }
    is_complex = bool(constraint_phrases) or _is_complex_query(seg)
    lower_clean_query = _normalize_text(clean_query)

    if constraint_phrases and any(keyword in lower_clean_query for keyword in _SUBJECT_REGISTRATION_BIAS_KEYWORDS):
        return {
            "intent": "subject_registration_suggestion",
            "confidence": 0.95,
            "intent_source": "keyword_bias",
            "is_complex": True,
            "needs_agent": True,
            "constraints": constraints,
            "clean_query": clean_query,
            "node_trace": ["intent_router_node"],
        }

    if any(keyword in lower_clean_query for keyword in _GRADUATION_KEYWORDS):
        return {
            "intent": "graduation_progress",
            "confidence": 0.95,
            "intent_source": "keyword",
            "is_complex": True,
            "needs_agent": True,
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
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "intent_source": "tfidf",
                    "is_complex": is_complex,
                    "needs_agent": is_complex,
                    "constraints": constraints,
                    "clean_query": clean_query,
                    "node_trace": ["intent_router_node"],
                }
        except Exception as exc:
            print(f"[NODE2] TF-IDF failed: {exc}")

    if clean_query:
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
            return {
                "intent": intent,
                "confidence": confidence,
                "intent_source": "openai",
                "is_complex": is_complex,
                "needs_agent": True,
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

    if intent not in ("unknown", None, ""):
        try:
            tools = _get_tools()

            raw_data = await asyncio.wait_for(
                tools.call(
                    intent,
                    {
                        "q": state.get("clean_query", seg),
                        "student_id": state.get("student_id"),
                        "conversation_id": state.get("conversation_id"),
                    },
                ),
                timeout=TOOL_EXECUTION_TIMEOUT,
            )
        except Exception as exc:
            raw_data = {"status": "error", "error": str(exc)}

    return {
        "raw_data": raw_data,
        "needs_agent_filter": needs_agent_filter,
        "node_trace": ["tool_executor_node"],
    }


def agent_filter_node(state: AgentState) -> Dict[str, Any]:
    raw_data = state.get("raw_data")
    constraints = state.get("constraints", {})
    excluded = constraints.get("exclude_subjects", [])
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
        payload["data"] = filtered_rows
        if isinstance(raw_data, dict) and "status" in raw_data and "data" in raw_data:
            raw_data["data"] = payload
            filtered_data = raw_data
        else:
            filtered_data = payload

    return {"filtered_data": filtered_data, "node_trace": ["agent_filter_node"]}


def response_formatter_node(state: AgentState) -> Dict[str, Any]:
    raw = state.get("filtered_data") or state.get("raw_data")
    seg = state.get("segments", [""])[state.get("current_segment_index", 0)]
    intent = state.get("intent", "unknown")
    text = format_rule_based_response(raw, intent, seg)
    return {
        "final_response": text,
        "formatted_result": {
            "text": text,
            "from_cache": False,
            "model_used": "rule_based",
            "processing_time_ms": 0,
        },
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


def rule_based_fallback_node(state: AgentState) -> Dict[str, Any]:
    return {
        "used_fallback": True,
        "raw_data": {
            "text": "Mình chưa phân tích kịp yêu cầu trong thời gian cho phép. Bạn vui lòng thử lại hoặc chia nhỏ câu hỏi giúp mình.",
        },
        "node_trace": ["rule_based_fallback_node"],
    }
