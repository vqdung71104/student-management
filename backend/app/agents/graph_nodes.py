"""
graph_nodes.py — Pure node functions for the LangGraph chatbot pipeline.

Mỗi hàm nhận (state: AgentState) và trả về (state: AgentState).
Tất cả I/O (LLM calls, HTTP calls) được đặt trong try/except với fallback.

Nodes:
  1. query_splitter_node    — Tách câu hỏi compound theo 'sau đó' / 'đồng thời'
  2. intent_router_node     — Constraint Stripping → TF-IDF trên clean_query
  3. constraint_parser_node — LLM trích xuất constraints (complex query only)
  4. tool_executor_node     — Gọi Tool + bắt buộc agent_filter với subject_registration
  5. agent_filter_node      — LLM đối chiếu raw_data với constraints
  6. response_formatter_node — LLM format cho 1 segment
  7. synthesize_formatter_node — LLM tổng hợp tất cả segment_results thành 1 câu trả lời
  8. rule_based_fallback_node  — Gọi Tool thủ công + Formatter (khi timeout/error)

Conditional Edges:
  9. route_decision  — Quyết định nhánh: rule_based | agent
 10. should_filter   — Quyết định agent_filter: always for subject_registration | if constraints exist
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
import traceback
from typing import Any, Dict, List, Optional

from app.llm.llm_client import LLMClient
from app.llm.llm_client import LLMCircuitOpenError, LLMAPIError, LLMTimeoutError
from app.llm.response_cache import ResponseCache
from app.agents.orchestration_metrics import get_orchestration_metrics
from app.agents.tools_registry import ToolsRegistry
from app.agents.graph_state import AgentState, PERIOD_TIME_KNOWLEDGE

try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "48"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "30.0"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "12"))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "20.0"))
NODE4_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "150"))
NODE4_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.1"))
NODE4_GENERATE_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
NODE4_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
NODE4_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "10.0"))
AGENT_REASONING_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "10.0"))
AGENT_EXTRACT_MAX_TOKENS = int(os.environ.get("AGENT_EXTRACT_MAX_TOKENS", "64"))
AGENT_FILTER_MAX_TOKENS = int(os.environ.get("AGENT_FILTER_MAX_TOKENS", "128"))

# Fields trimmed before sending to formatter
_TRIM_FIELDS = frozenset({
    "_student_course_pk", "_in_student_program", "_student_learning_status",
    "_student_grade_history", "_student_latest_grade", "_student_latest_semester",
    "_student_course_name", "_student_context_message", "_intent_type",
    "_id", "_score", "_rank",
})
_MAX_ITEMS_PER_LIST = 20

# Constraint keywords → marks query as "complex"
_CONSTRAINT_KEYWORDS = frozenset({
    "không muốn", "ngoại trừ", "tránh", "lúc", "thay vì",
    "không học", "sau", "trước",
})

# Multi-intent connectors: trigger segment split
_MULTI_INTENT_PATTERNS = frozenset({
    " sau đó ", " sau đó,", "đồng thời", "và", " rồi ", " tiếp theo ",
    " sau đó. ", " và ", " luôn ", " vừa ", " vừa...vừa ",
})

# Node-3 subtype mapping
_NODE3A_INTENTS = frozenset({
    "subject_info", "class_info", "grade_view",
    "learned_subjects_view", "schedule_view", "schedule_info", "student_info",
})
_NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})
_NODE3C_INTENTS = frozenset({"class_registration_suggestion"})
_NODE3D_INTENTS = frozenset({"modify_schedule"})

# ──────────────────────────────────────────────────────────────────────────────
# Shared singletons
# ──────────────────────────────────────────────────────────────────────────────
_llm_client: Optional[LLMClient] = None
_tools_registry: Optional[ToolsRegistry] = None
_response_cache: Optional[ResponseCache] = None
_tfidf_classifier = TfidfIntentClassifier() if TfidfIntentClassifier else None
_metrics = get_orchestration_metrics()


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


def _get_cache() -> ResponseCache:
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache


def _is_complex_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _CONSTRAINT_KEYWORDS)


def _has_multi_intent(text: str) -> bool:
    """Return True if text contains multi-intent connectors (sau đó, đồng thời, ...)."""
    lower = text.lower()
    return any(pat in lower for pat in _MULTI_INTENT_PATTERNS)


def _resolve_node3_subtype(intent: Optional[str]) -> Optional[str]:
    if intent in _NODE3A_INTENTS:
        return "node3a"
    if intent in _NODE3B_INTENTS:
        return "node3b"
    if intent in _NODE3C_INTENTS:
        return "node3c"
    if intent in _NODE3D_INTENTS:
        return "node3d"
    return None


def _preview(value: Any, max_len: int = 140) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        text = str(value)
    return text[:max_len] + "..." if len(text) > max_len else text


def _trim_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _trim_data(v) for k, v in data.items() if k not in _TRIM_FIELDS}
    if isinstance(data, list):
        if len(data) > _MAX_ITEMS_PER_LIST:
            return _trim_data(data[:_MAX_ITEMS_PER_LIST])
        return [_trim_data(item) for item in data]
    return data


def _compact_data(raw: Any) -> str:
    """Compact raw data for minimal token usage in prompts."""
    trimmed = _trim_data(raw)
    if isinstance(trimmed, list):
        lines = []
        for i, item in enumerate(trimmed):
            if isinstance(item, dict):
                essential = {
                    k: v for k, v in item.items()
                    if isinstance(v, (str, int, float, bool)) or (isinstance(v, list) and len(v) <= 5)
                }
                parts = [f"{k}={v}" for k, v in essential.items() if v is not None][:10]
                lines.append(", ".join(parts))
            else:
                lines.append(str(item)[:100])
        return "\n".join(lines)[:2000]
    return str(trimmed)[:1000]


def _hash_for_cache(raw: Any, instruction: str) -> str:
    import hashlib

    def _stable(val: Any) -> str:
        try:
            return json.dumps(val, ensure_ascii=False, sort_keys=True, default=str)
        except TypeError:
            return str(val)

    raw_bytes = _stable({"instruction": instruction, "raw": raw}).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()


def _extract_result_data(raw_result: Any) -> Any:
    if raw_result is None:
        return None
    if isinstance(raw_result, dict):
        if "status" in raw_result and "data" in raw_result:
            inner = raw_result["data"]
            return _extract_result_data(inner)
        if "segment" in raw_result or "raw_result" in raw_result:
            inner = raw_result.get("raw_result", raw_result)
            return _extract_result_data(inner)
        text_val = raw_result.get("text")
        if isinstance(text_val, str) and text_val.strip():
            return raw_result
        return raw_result
    if isinstance(raw_result, list):
        if len(raw_result) == 0:
            return None
        if len(raw_result) == 1:
            return _extract_result_data(raw_result[0])
        return [_extract_result_data(item) for item in raw_result]
    return raw_result


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
        for key in ["data", "result", "text", "rows", "items"]:
            if key in data:
                val = data[key]
                if val is not None and not (isinstance(val, list) and len(val) == 0):
                    return False
        text_val = data.get("text")
        if isinstance(text_val, str) and text_val.strip():
            return False
        if not any(k in data for k in ["data", "result", "text", "rows", "items"]):
            return True
    if isinstance(data, str) and not data.strip():
        return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# NODE 1: query_splitter_node
# Multi-intent detection via 'sau đó', 'đồng thời', 'và', 'rồi'
# Constraint guard: never split if constraints are present
# ──────────────────────────────────────────────────────────────────────────────
def query_splitter_node(state: AgentState) -> AgentState:
    """
    Tách câu hỏi compound thành các segment đơn.

    Multi-intent connectors: 'sau đó', 'đồng thời', 'và', 'rồi', 'tiếp theo'

    Constraint guard: nếu câu hỏi chứa constraint keywords
    (không muốn, tránh, ngoại trừ, không học, thay vì, sau, trước),
    tuyệt đối KHÔNG TÁCH — giữ nguyên toàn bộ câu.
    """
    text = state.get("user_text", "")
    started = time.perf_counter()

    # ── GUARD: Never split if constraints are present ───────────────────────────
    if _is_complex_query(text):
        _metrics.increment("node1.constraint_guard_hit")
        _metrics.observe_latency("node1.latency", time.perf_counter() - started)
        print(f"[NODE1] CONSTRAINT GUARD → 1 segment")
        return {
            **state,
            "segments": [text],
            "node_trace": state.get("node_trace", []) + ["query_splitter_node"],
        }

    # ── Trivial case: short simple query ───────────────────────────────────────
    if len(text.split()) < 40 and ('?' not in text and ',' not in text and '.' not in text):
        _metrics.increment("node1.heuristic_hit")
        _metrics.observe_latency("node1.latency", time.perf_counter() - started)
        return {
            **state,
            "segments": [text],
            "node_trace": state.get("node_trace", []) + ["query_splitter_node"],
        }

    # ── Multi-intent detection: split on connectors ─────────────────────────────
    # Patterns ordered by specificity (most specific first)
    _SPLIT_PATTERN = re.compile(
        r'(?<=[,;])\s*(?:sau đó|đồng thời|rồi|tiếp theo)\b|'
        r'\s+(?:sau đó|đồng thời)\s+|'
        r'\s+và\s+|'
        r'\s+vừa\s+',
        re.IGNORECASE,
    )

    if _SPLIT_PATTERN.search(text):
        # Split on multi-intent connectors
        parts = _SPLIT_PATTERN.split(text)
        segments = [p.strip() for p in parts if p.strip()]
        if len(segments) >= 2:
            _metrics.increment("node1.multi_intent_split")
            _metrics.observe_latency("node1.latency", time.perf_counter() - started)
            print(f"[NODE1] multi-intent split → {len(segments)} segments")
            return {
                **state,
                "segments": segments,
                "node_trace": state.get("node_trace", []) + ["query_splitter_node"],
            }

    # ── Fallback: LLM split for complex compound queries ───────────────────────
    llm = _get_llm()
    try:
        async def _llm_split():
            return await llm.split(
                text,
                timeout=NODE1_TIMEOUT,
                max_tokens=NODE1_SPLIT_MAX_TOKENS,
                temperature=0.0,
            )

        res = asyncio.run(_llm_split())
        segments = res.get("segments") or [text]
        _metrics.increment("node1.llm_success")
        _metrics.observe_latency("node1.latency", time.perf_counter() - started)
        print(f"[NODE1] LLM split → {len(segments)} segments")
    except Exception as exc:
        _metrics.increment("node1.fallback")
        _metrics.observe_latency("node1.latency", time.perf_counter() - started)
        segments = [text]
        print(f"[NODE1] LLM split failed: {exc} → 1 segment")

    return {
        **state,
        "segments": segments,
        "node_trace": state.get("node_trace", []) + ["query_splitter_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 2: intent_router_node  — CONSTRAINT STRIPPING + TF-IDF on clean_query
# ──────────────────────────────────────────────────────────────────────────────

# Regex patterns to find constraint phrases in queries
_CONSTRAINT_PREFIX_PATTERNS = [
    # sau các từ khóa → phần ràng buộc
    re.compile(
        r'\b(?:'
        r'không\s+muốn\s+|'
        r'ngoại\s+trừ\s+|'
        r'tránh\s+|'
        r'không\s+học\s+|'
        r'thay\s+vì\s+|'
        r'sau\s+)'
        r'([^\.,;]+)',
        re.IGNORECASE,
    ),
    # "tránh môn X" — giữ nguyên cụm "tránh môn X"
    re.compile(
        r'(tránh\s+(?:môn|học phần|lớp)\s*\S[^\.,;]*)',
        re.IGNORECASE,
    ),
    # "ngoại trừ môn X"
    re.compile(
        r'(ngoại\s+trừ\s+(?:môn|học phần)\s*\S[^\.,;]*)',
        re.IGNORECASE,
    ),
]


def _strip_constraints(text: str) -> tuple[str, List[str]]:
    """
    Trích xuất các cụm từ ràng buộc khỏi câu query và trả về:
      - clean_query: câu query đã cắt bỏ các cụm ràng buộc
      - constraint_phrases: danh sách các cụm từ bị cắt

    Ví dụ:
      'Tôi muốn đăng ký học phần, tránh môn X'
      → clean_query = 'Tôi muốn đăng ký học phần'
      → constraint_phrases = ['tránh môn X']
    """
    constraint_phrases: List[str] = []
    clean = text

    for pattern in _CONSTRAINT_PREFIX_PATTERNS:
        for match in pattern.finditer(clean):
            phrase = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if phrase and len(phrase) > 2 and phrase.lower() not in ("và", "sau", "trước", "tránh", "ngoại trừ"):
                constraint_phrases.append(phrase)

    # Remove constraint phrases from query
    for phrase in constraint_phrases:
        # Remove the phrase and clean up extra spaces/punctuation
        clean = re.sub(re.escape(phrase), '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s{2,}', ' ', clean)  # collapse multiple spaces
        clean = re.sub(r'[,;]\s*[,;]', ',', clean)  # collapse double punctuation

    clean = clean.strip()
    # Clean up trailing punctuation
    clean = re.sub(r'[,;]\s*$', '', clean).strip()
    if not clean:
        clean = text  # fallback: keep original if stripping removes everything

    return clean, constraint_phrases


def intent_router_node(state: AgentState) -> AgentState:
    """
    Phân loại intent cho segment hiện tại.

    Yêu cầu kỹ thuật — CONSTRAINT STRIPPING:
      1. Trước khi gọi TF-IDF, trích xuất constraint phrases (sau 'không muốn', 'tránh', 'ngoại trừ').
      2. Cắt bỏ chúng khỏi câu query → clean_query.
      3. TF-IDF chạy trên clean_query.
      4. Lưu constraint_phrases vào state['constraints']['constraint_phrases'].

    Ví dụ:
      'Tôi muốn đăng ký học phần, tránh môn X'
      → clean_query = 'Tôi muốn đăng ký học phần'
      → Intent = subject_registration_suggestion (from clean_query)
      → Constraints: exclude_subjects = ['X']
    """
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")

    # Determine complexity from original full query
    original_text = state.get("user_text", "")
    is_complex = _is_complex_query(original_text)
    needs_agent = is_complex

    started = time.perf_counter()

    # ── Step 1: Constraint Stripping ────────────────────────────────────────────
    clean_query, constraint_phrases = _strip_constraints(seg)
    constraints: Dict[str, Any] = {
        "constraint_phrases": constraint_phrases,
        "exclude_subjects": [],
        "forbidden_time_slots": [],
        "forbidden_times": [],
        "semester": None,
        "days": [],
    }

    # Parse exclude_subjects from constraint_phrases using LLM (lightweight)
    if constraint_phrases:
        try:
            async def _parse():
                llm = _get_llm()
                phrases_str = ", ".join(f'"{p}"' for p in constraint_phrases)
                prompt = (
                    f"Bạn là trợ lý học vụ. Trích xuất danh sách mã môn học từ các cụm từ sau.\n"
                    f"Cụm từ: [{phrases_str}]\n\n"
                    f"Trả về JSON thuần: {{'exclude_subjects': ['IT1111', ...]}}\n"
                    f"Nếu không có mã môn nào, trả về: {{'exclude_subjects': []}}"
                )
                res = await llm.classify(prompt, timeout=5.0, max_tokens=64, temperature=0.0)
                return json.loads(res.get("text", "{}"))
            parsed = asyncio.run(_parse())
            if isinstance(parsed, dict) and "exclude_subjects" in parsed:
                constraints["exclude_subjects"] = parsed["exclude_subjects"]
        except Exception as exc:
            print(f"[NODE2] constraint parse failed: {exc}")

    print(f"[NODE2] strip → clean_query={_preview(clean_query, 80)} "
          f"constraint_phrases={constraint_phrases}")

    # ── Step 2: TF-IDF on clean_query ─────────────────────────────────────────
    intent = "unknown"
    confidence = 0.0
    source = "fallback"

    if _tfidf_classifier and clean_query:
        try:
            async def _classify():
                return await _tfidf_classifier.classify_intent(clean_query)

            tfidf_res = asyncio.run(_classify())
            intent = tfidf_res.get("intent", "unknown")
            confidence = float(tfidf_res.get("confidence_score", 0.0))

            if confidence >= INTENT_CONF_THRESHOLD or len(clean_query.split()) <= 20:
                _metrics.increment("node2.tfidf_hit")
                _metrics.observe_latency("node2.latency", time.perf_counter() - started)
                print(f"[NODE2] TF-IDF → intent={intent} conf={confidence:.3f} "
                      f"needs_agent={needs_agent} (is_complex={is_complex})")
                return {
                    **state,
                    "intent": intent,
                    "confidence": confidence,
                    "intent_source": "tfidf",
                    "is_complex": is_complex,
                    "needs_agent": needs_agent,
                    "constraints": constraints,
                    "clean_query": clean_query,
                    "node_trace": state.get("node_trace", []) + ["intent_router_node"],
                }
        except Exception as exc:
            print(f"[NODE2] TF-IDF failed: {exc}")

    # ── Step 3: LLM fallback on clean_query ───────────────────────────────────
    try:
        llm = _get_llm()
        combined_prompt = (
            "Bạn là trợ lý học vụ.\n"
            + PERIOD_TIME_KNOWLEDGE
            + f"\nCâu hỏi (sau khi loại bỏ ràng buộc): {clean_query}\n\n"
            "Trả về JSON thuần với 2 trường:\n"
            "{\n"
            '  "intent": "<intent>",\n'
            '  "confidence": 0.0,\n'
            '  "constraints": {\n'
            '    "exclude_subjects": [],\n'
            '    "forbidden_time_slots": [],\n'
            '    "forbidden_times": [],\n'
            '    "semester": null,\n'
            '    "days": []\n'
            "  }\n"
            "}\n"
            "intent là một trong: subject_registration_suggestion, class_registration_suggestion, "
            "class_info, schedule_view, grade_view, learned_subjects_view, subject_info, "
            "student_info, modify_schedule, greeting, thanks, unknown"
        )
        res = asyncio.run(llm.classify(
            combined_prompt,
            timeout=NODE2_TIMEOUT,
            max_tokens=NODE2_CLASSIFY_MAX_TOKENS,
            temperature=0.0,
        ))

        intent_raw = res.get("intent") or res.get("label") or "unknown"
        confidence = max(0.0, min(1.0, float(res.get("confidence", 0.6))))
        try:
            text = res.get("text", "")
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                intent = parsed.get("intent", intent_raw)
                llm_constraints = parsed.get("constraints") or {}
                # Merge LLM constraints into our constraints dict
                for k, v in llm_constraints.items():
                    if k in constraints:
                        constraints[k] = v
            else:
                intent = intent_raw
        except (json.JSONDecodeError, TypeError):
            intent = intent_raw

        source = "llm"
        _metrics.increment("node2.llm_success")
        _metrics.observe_latency("node2.latency", time.perf_counter() - started)
        print(f"[NODE2] LLM → intent={intent} conf={confidence:.3f} needs_agent={needs_agent}")
    except Exception as exc:
        _metrics.increment("node2.fallback")
        _metrics.observe_latency("node2.latency", time.perf_counter() - started)
        print(f"[NODE2] LLM fallback: {exc}")

    return {
        **state,
        "intent": intent,
        "confidence": confidence,
        "intent_source": source,
        "is_complex": is_complex,
        "needs_agent": needs_agent,
        "constraints": constraints,
        "clean_query": clean_query,
        "node_trace": state.get("node_trace", []) + ["intent_router_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 3: constraint_parser_node  (complex queries only)
# ──────────────────────────────────────────────────────────────────────────────
CONSTRAINT_EXTRACT_PROMPT = (
    "Bạn là trợ lý học vụ chuyên trích xuất ràng buộc từ câu hỏi sinh viên.\n"
    + PERIOD_TIME_KNOWLEDGE
    + "\nCâu hỏi: {query}\n\n"
    "Trả về JSON thuần (không giải thích) với các trường sau:\n"
    "{\n"
    '  "exclude_subjects": [],       // list mã môn học cần loại bỏ (VD: ["IT1111"])\n'
    '  "forbidden_time_slots": [],   // list số tiết cần tránh (VD: [1,2,3,4,5] cho sáng)\n'
    '  "forbidden_times": [],        // list giờ cụ thể cần tránh (VD: ["06:45", "17:30"])\n'
    '  "semester": null,            // kỳ học nếu có\n'
    '  "days": []                   // các thứ ưu tiên (VD: ["Monday","Tuesday"])\n'
    "}\n"
    "Nếu không có ràng buộc nào: {\"exclude_subjects\":[],\"forbidden_time_slots\":[],\"forbidden_times\":[],\"semester\":null,\"days\":[]}"
)


def constraint_parser_node(state: AgentState) -> AgentState:
    """
    Trích xuất ràng buộc ngữ nghĩa từ câu hỏi phức tạp qua LLM.

    PERFORMANCE: Nếu intent_router_node đã extract constraints trong cùng 1 LLM call,
    state['constraints'] đã có dữ liệu → skip LLM call.
    """
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")
    llm = _get_llm()
    started = time.perf_counter()

    # PERFORMANCE: Skip if router already extracted constraints
    existing_constraints = state.get("constraints")
    if existing_constraints and isinstance(existing_constraints, dict):
        non_empty = any(
            v for k, v in existing_constraints.items()
            if k != "constraint_phrases" and v and v != [] and v != {}
        )
        if non_empty or existing_constraints.get("constraint_phrases"):
            _metrics.increment("constraint_parser.skipped_already_extracted")
            print(f"[CONSTRAINT_PARSER] skipped — already extracted: {existing_constraints}")
            return {
                **state,
                "constraints": existing_constraints,
                "node_trace": state.get("node_trace", []) + ["constraint_parser_node"],
            }

    # Build default constraints
    constraints: Dict[str, Any] = {
        "constraint_phrases": [],
        "exclude_subjects": [],
        "forbidden_time_slots": [],
        "forbidden_times": [],
        "semester": None,
        "days": [],
    }

    try:
        async def _extract():
            prompt = CONSTRAINT_EXTRACT_PROMPT.format(query=seg)
            return await llm.classify(
                prompt,
                timeout=AGENT_REASONING_TIMEOUT / 3,
                max_tokens=AGENT_EXTRACT_MAX_TOKENS,
                temperature=0.0,
            )

        res = asyncio.run(_extract())
        text = res.get("text", "")
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k in constraints:
                    constraints[k] = v
        _metrics.increment("constraint_parser.success")
        _metrics.observe_latency("constraint_parser.latency", time.perf_counter() - started)
        print(f"[CONSTRAINT_PARSER] → {constraints}")
    except json.JSONDecodeError:
        _metrics.increment("constraint_parser.parse_error")
        print(f"[CONSTRAINT_PARSER] JSON parse failed")
    except Exception as exc:
        _metrics.increment("constraint_parser.error")
        print(f"[CONSTRAINT_PARSER] error: {exc}")

    return {
        **state,
        "constraints": constraints,
        "node_trace": state.get("node_trace", []) + ["constraint_parser_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 4: tool_executor_node
# Yêu cầu: subject_registration_suggestion → bắt buộc phải qua agent_filter_node
#           class_info → SQL query dựa trên subject_id hoặc tên môn
# ──────────────────────────────────────────────────────────────────────────────
def tool_executor_node(state: AgentState) -> AgentState:
    """
    Gọi Tool để lấy dữ liệu thô.

    Kỹ thuật:
      - subject_registration_suggestion: sau khi lấy raw_data, bắt buộc đi qua
        agent_filter_node (filtered_data sẽ được ghi đè bởi agent_filter).
      - class_info: truy vấn dựa trên subject_id hoặc tên môn được trích xuất.
      - Node trả về flag 'needs_agent_filter' để graph quyết định routing.
    """
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")
    intent = state.get("intent", "unknown")
    student_id = state.get("student_id")
    conversation_id = state.get("conversation_id")
    tools = _get_tools()
    started = time.perf_counter()

    raw_data: Any = {"message": "No tool mapped", "items": []}
    needs_agent_filter = False

    # Determine if agent_filter is required
    if intent in _NODE3B_INTENTS:  # subject_registration_suggestion
        needs_agent_filter = True
    elif state.get("constraints"):
        c = state.get("constraints", {})
        if any(c.get(k) for k in ("exclude_subjects", "forbidden_time_slots", "forbidden_times", "days") if c.get(k)):
            needs_agent_filter = True

    if intent and intent not in frozenset({"greeting", "thanks", "unknown", None, ""}):
        try:
            async def _call():
                return await tools.call(intent, {
                    "q": seg,
                    "student_id": student_id,
                    "conversation_id": conversation_id,
                })

            raw_data = asyncio.run(_call())
            _metrics.increment(f"tools.{intent}.success")
            _metrics.observe_latency(f"tools.{intent}.latency", time.perf_counter() - started)
            print(f"[TOOL] intent={intent} done in {(time.perf_counter()-started)*1000:.1f}ms "
                  f"needs_agent_filter={needs_agent_filter}")
        except Exception as exc:
            _metrics.increment(f"tools.{intent or 'unknown'}.failure")
            err = f"TOOLS_LAYER_UNEXPECTED: {type(exc).__name__}: {exc}"
            print(f"[TOOL] error: {err}")
            raw_data = {"status": "error", "error": err}
    else:
        _metrics.increment("tools.skipped_unknown_intent")

    return {
        **state,
        "raw_data": raw_data,
        "needs_agent_filter": needs_agent_filter,
        "node_trace": state.get("node_trace", []) + ["tool_executor_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 5: agent_filter_node
# LLM đối chiếu raw_data với constraints (bắt buộc với subject_registration_suggestion)
# ──────────────────────────────────────────────────────────────────────────────
CONSTRAINT_FILTER_PROMPT = (
    "Bạn là trợ lý học vụ. Lọc danh sách theo ràng buộc của sinh viên.\n"
    + PERIOD_TIME_KNOWLEDGE
    + "\nRàng buộc: {constraints}\n\n"
    "Dữ liệu thô (danh sách lớp/môn):\n{data}\n\n"
    "Quy tắc:\n"
    "  - Nếu exclude_subjects chứa mã môn, loại bỏ mọi row có subject_code hoặc subject_id tương ứng.\n"
    "  - Nếu forbidden_time_slots chứa số tiết, loại bỏ các row có study_time_slot nằm trong danh sách.\n"
    "  - Nếu forbidden_times chứa giờ bắt đầu, loại bỏ các row trùng giờ.\n"
    "  - Giữ nguyên các row không vi phạm ràng buộc nào.\n"
    "Trả về JSON thuần:\n"
    "{{'status': 'success', 'data': <danh_sách_đã_lọc>}}\n"
    "Nếu tất cả bị loại, trả về: {{'status': 'success', 'data': []}}"
)


def agent_filter_node(state: AgentState) -> AgentState:
    """
    LLM đối chiếu raw_data với constraints.

    Bắt buộc chạy khi:
      - intent = subject_registration_suggestion
      - hoặc constraints có bất kỳ filter nào (exclude_subjects, forbidden_time_slots, ...)

    Fallback: dùng raw_data nếu LLM filter thất bại.
    """
    raw_data = state.get("raw_data")
    constraints = state.get("constraints") or {}
    llm = _get_llm()
    started = time.perf_counter()

    # Only filter if there are actual constraints to apply
    has_constraints = any(
        constraints.get(k)
        for k in ("exclude_subjects", "forbidden_time_slots", "forbidden_times", "days")
        if constraints.get(k)
    )
    if not has_constraints:
        _metrics.increment("agent_filter.skipped_no_constraints")
        print("[AGENT_FILTER] skipped — no constraints to apply")
        return {
            **state,
            "filtered_data": raw_data,
            "node_trace": state.get("node_trace", []) + ["agent_filter_node"],
        }

    filtered_data = raw_data

    try:
        async def _filter():
            compact = _compact_data(raw_data)
            prompt = CONSTRAINT_FILTER_PROMPT.format(
                constraints=json.dumps(constraints, ensure_ascii=False),
                data=compact,
            )
            return await llm.generate(
                prompt,
                timeout=AGENT_REASONING_TIMEOUT / 2,
                max_tokens=AGENT_FILTER_MAX_TOKENS,
                temperature=0.1,
            )

        res = asyncio.run(_filter())
        text = res.get("text", "")
        parsed = json.loads(text)
        filtered_data = parsed if isinstance(parsed, dict) else raw_data
        _metrics.increment("agent_filter.success")
        _metrics.observe_latency("agent_filter.latency", time.perf_counter() - started)
        print(f"[AGENT_FILTER] filtered → {type(filtered_data).__name__}")
    except json.JSONDecodeError:
        _metrics.increment("agent_filter.parse_error")
        print(f"[AGENT_FILTER] JSON parse failed, using raw_data")
    except Exception as exc:
        _metrics.increment("agent_filter.error")
        print(f"[AGENT_FILTER] error: {exc}")

    return {
        **state,
        "filtered_data": filtered_data,
        "node_trace": state.get("node_trace", []) + ["agent_filter_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 6: response_formatter_node (per-segment)
# ──────────────────────────────────────────────────────────────────────────────
FEW_SHOT = """
## Ví dụ trả lời (few-shot):
Ví dụ 1:
- Dữ liệu: {"cpa": 3.3}
- Câu hỏi: CPA của tôi là bao nhiêu?
- Trả lời: CPA hiện tại của bạn là 3.3.

Ví dụ 2:
- Dữ liệu: [{"subject_name": "Toán A1", "letter_grade": "A"}]
- Câu hỏi: Điểm của tôi các môn này thế nào?
- Trả lời: Bạn đã học môn Toán A1 với điểm A.

Ví dụ 3:
- Dữ liệu: []
- Câu hỏi: Tôi đã đăng ký những môn nào?
- Trả lời: Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. Bạn vui lòng kiểm tra lại nhé!

Ví dụ 4:
- Dữ liệu: {"subject_name": "Ngữ văn 1", "credits": 3, "teacher_name": "Nguyễn Văn A"}
- Câu hỏi: Thông tin môn Ngữ văn 1?
- Trả lời: Môn Ngữ văn 1 có 3 tín chỉ, giảng viên Nguyễn Văn A.
"""


def response_formatter_node(state: AgentState) -> AgentState:
    """
    Format raw/filtered data thành câu trả lời thân thiện qua LLM.
    Sử dụng cached response nếu có.
    """
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")
    intent = state.get("intent", "unknown")
    raw = state.get("filtered_data") or state.get("raw_data")
    llm = _get_llm()
    cache = _get_cache()
    started = time.perf_counter()

    segment_results = state.get("segment_results", [])
    intent_hints = [
        r.get("intent", {}).get("intent") if isinstance(r.get("intent"), dict) else r.get("intent")
        for r in segment_results
    ]
    if intent:
        intent_hints.append(intent)

    text = ""
    from_cache = False
    model_used = "none"
    llm_ms = 0.0

    # Handle error status
    if isinstance(raw, dict) and raw.get("status") == "error":
        _metrics.increment("node4.tool_error_status")
        _metrics.observe_latency("node4.latency", time.perf_counter() - started)
        text = (
            "Mình gặp một chút trục trặc khi xử lý yêu cầu này. "
            "Bạn vui lòng thử lại hoặc diễn đạt câu hỏi theo cách khác nhé!"
        )
        model_used = "error_status"
        print("[NODE4] error status from tool")
    elif _is_data_empty(raw):
        _metrics.increment("node4.empty_data")
        _metrics.observe_latency("node4.latency", time.perf_counter() - started)
        text = "Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. Bạn vui lòng kiểm tra lại nhé!"
        model_used = "empty_guard"
    else:
        # Cache check
        h = _hash_for_cache(raw, seg)
        cached = cache.get(h)
        if cached:
            _metrics.increment("node4.cache_hit")
            _metrics.observe_latency("node4.latency", time.perf_counter() - started)
            text = cached
            from_cache = True
            model_used = "cache"
        else:
            _metrics.increment("node4.cache_miss")
            extracted = _extract_result_data(raw)
            try:
                json_data = json.dumps(extracted, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                json_data = str(extracted) if extracted is not None else "{}"

            prompt = (
                f"Dữ liệu hệ thống trả về: {json_data}\n"
                f"Câu hỏi người dùng: {seg}\n"
                f"Intent: {', '.join(str(i) for i in intent_hints if i)}\n\n"
                "Hãy trả lời bằng tiếng Việt, ngắn gọn, chuyên nghiệp theo phong cách trợ lý học vụ.\n"
                + FEW_SHOT
            )

            try:
                async def _generate():
                    return await llm.generate(
                        prompt,
                        max_tokens=NODE4_GENERATE_MAX_TOKENS,
                        temperature=NODE4_GENERATE_TEMPERATURE,
                        timeout=NODE4_TIMEOUT,
                        top_p=NODE4_GENERATE_TOP_P,
                        repeat_penalty=NODE4_REPEAT_PENALTY,
                    )

                gen_started = time.perf_counter()
                res = asyncio.run(_generate())
                text = (res.get("text") or str(res) or "").strip()
                model_used = res.get("model_used", "openai")
                llm_ms = (time.perf_counter() - gen_started) * 1000
                _metrics.increment("node4.llm_success")
                _metrics.observe_latency("node4.latency", time.perf_counter() - started)

                if not text:
                    raise ValueError("LLM returned empty text")

                cache.set(h, text)
            except LLMCircuitOpenError:
                _metrics.increment("node4.circuit_open")
                text = "Hệ thống đang bận, bạn vui lòng thử lại trong giây lát nhé!"
                model_used = "circuit_open"
            except (asyncio.TimeoutError, LLMTimeoutError):
                _metrics.increment("node4.timeout")
                text = "Mình đang xử lý hơi chậm, bạn vui lòng thử lại trong giây lát nhé!"
                model_used = "timeout"
            except LLMAPIError:
                _metrics.increment("node4.api_error")
                text = "Mình gặp chút trục trặc khi xử lý câu trả lời, bạn vui lòng thử lại nhé!"
                model_used = "api_error"
            except Exception as exc:
                _metrics.increment("node4.fallback")
                print(f"[NODE4] unexpected error: {exc}\n{traceback.format_exc()}")
                text = "Mình gặp chút trục trặc khi xử lý câu trả lời, bạn vui lòng thử lại nhé!"
                model_used = "error"

    print(f"[NODE4] done model={model_used} from_cache={from_cache}")
    return {
        **state,
        "final_response": text,
        "formatted_result": {
            "text": text,
            "from_cache": from_cache,
            "model_used": model_used,
            "processing_time_ms": llm_ms,
        },
        "node_trace": state.get("node_trace", []) + ["response_formatter_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 7: synthesize_formatter_node
# Tổng hợp kết quả từ TẤT CẢ các segment trong segment_results
# thành MỘT câu trả lời duy nhất, tự nhiên, bao quát toàn bộ yêu cầu theo đúng thứ tự
# ──────────────────────────────────────────────────────────────────────────────
def synthesize_formatter_node(state: AgentState) -> AgentState:
    """
    LLM tổng hợp tất cả kết quả segment trong state['segment_results']
    thành một câu trả lời duy nhất, tự nhiên, theo đúng thứ tự hỏi.

    Chỉ gọi khi có >= 2 segment.
    """
    segment_results = state.get("segment_results", [])
    user_text = state.get("user_text", "")
    llm = _get_llm()
    cache = _get_cache()
    started = time.perf_counter()

    if len(segment_results) < 2:
        # Single segment — no synthesis needed, just return the existing response
        print("[SYNTHESIZE] single segment → pass through")
        return {
            **state,
            "node_trace": state.get("node_trace", []) + ["synthesize_formatter_node"],
        }

    # Build synthesis prompt from all segment results
    lines = []
    for i, seg_result in enumerate(segment_results, start=1):
        seg_text = seg_result.get("segment", "")
        raw = seg_result.get("raw_result")
        # Extract text from raw
        if isinstance(raw, dict):
            if raw.get("status") == "error":
                res_text = f"[Lỗi: {raw.get('error', 'unknown')}]"
            elif raw.get("text") and raw.get("is_preference_collecting"):
                res_text = raw.get("text", "")
            else:
                extracted = _extract_result_data(raw)
                try:
                    res_text = json.dumps(extracted, ensure_ascii=False, default=str)[:500]
                except Exception:
                    res_text = str(extracted)[:500] if extracted else ""
        elif isinstance(raw, list):
            res_text = f"[{len(raw)} kết quả]"
        else:
            res_text = str(raw)[:500] if raw else ""

        intent_label = "unknown"
        intent_info = seg_result.get("intent")
        if isinstance(intent_info, dict):
            intent_label = intent_info.get("intent", "unknown")
        elif intent_info:
            intent_label = str(intent_info)

        lines.append(f"--- Segment {i} ---")
        lines.append(f"Câu hỏi: {seg_text}")
        lines.append(f"Intent: {intent_label}")
        lines.append(f"Kết quả: {res_text}")
        lines.append("")

    segments_context = "\n".join(lines)
    synthesis_prompt = (
        "Bạn là trợ lý học vụ. Tổng hợp các kết quả từ nhiều câu hỏi thành MỘT câu trả lời duy nhất, "
        "tự nhiên, ngắn gọn, chuyên nghiệp.\n\n"
        "YÊU CẦU:\n"
        "  1. Trả lời bao quát TẤT CẢ các câu hỏi theo ĐÚNG THỨ TỰ người dùng hỏi.\n"
        "  2. Dùng tiếng Việt, phong cách trợ lý học vụ.\n"
        "  3. Không lặp lại thông tin, không thừa, không thiếu.\n"
        "  4. Nếu có câu hỏi không tìm thấy kết quả, nói rõ và chuyển sang câu tiếp.\n"
        "  5. Nếu câu hỏi thứ 2 phụ thuộc kết quả câu 1 (VD: 'sau đó'), đảm bảo logic.\n\n"
        f"Câu hỏi gốc: {user_text}\n\n"
        f"Kết quả từng phần:\n{segments_context}\n\n"
        "Trả lời:"
    )

    # Cache check
    cache_key = f"synthesize_{len(segment_results)}_{hash(segments_context) % 10**8}"
    cached = cache.get(cache_key)
    if cached:
        _metrics.increment("node4_synthesize.cache_hit")
        _metrics.observe_latency("node4_synthesize.latency", time.perf_counter() - started)
        print(f"[SYNTHESIZE] cache hit ({len(segment_results)} segments)")
        return {
            **state,
            "final_response": cached,
            "formatted_result": {
                "text": cached,
                "from_cache": True,
                "model_used": "cache",
                "processing_time_ms": 0.0,
                "synthesized": True,
            },
            "node_trace": state.get("node_trace", []) + ["synthesize_formatter_node"],
        }

    _metrics.increment("node4_synthesize.cache_miss")
    text = ""
    model_used = "none"
    llm_ms = 0.0

    try:
        async def _generate():
            return await llm.generate(
                synthesis_prompt,
                max_tokens=NODE4_GENERATE_MAX_TOKENS * 2,
                temperature=NODE4_GENERATE_TEMPERATURE,
                timeout=NODE4_TIMEOUT,
                top_p=NODE4_GENERATE_TOP_P,
                repeat_penalty=NODE4_REPEAT_PENALTY,
            )

        gen_started = time.perf_counter()
        res = asyncio.run(_generate())
        text = (res.get("text") or str(res) or "").strip()
        model_used = res.get("model_used", "openai")
        llm_ms = (time.perf_counter() - gen_started) * 1000
        _metrics.increment("node4_synthesize.llm_success")
        _metrics.observe_latency("node4_synthesize.latency", time.perf_counter() - started)

        if not text:
            raise ValueError("Synthesize LLM returned empty text")

        cache.set(cache_key, text)
    except Exception as exc:
        _metrics.increment("node4_synthesize.error")
        print(f"[SYNTHESIZE] error: {exc}\n{traceback.format_exc()}")
        text = "Mình gặp chút trục trặc khi tổng hợp kết quả, bạn vui lòng thử lại nhé!"
        model_used = "error"
        llm_ms = 0.0

    print(f"[SYNTHESIZE] done {len(segment_results)} segments → {len(text)} chars model={model_used}")
    return {
        **state,
        "final_response": text,
        "formatted_result": {
            "text": text,
            "from_cache": False,
            "model_used": model_used,
            "processing_time_ms": llm_ms,
            "synthesized": True,
        },
        "node_trace": state.get("node_trace", []) + ["synthesize_formatter_node"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# NODE 8: rule_based_fallback_node
# ──────────────────────────────────────────────────────────────────────────────
def rule_based_fallback_node(state: AgentState) -> AgentState:
    """
    Fallback khi agent branch vượt quá 10s hoặc gặp lỗi.
    1. Gọi Tool trực tiếp (không qua agent filter)
    2. Gắn thông báo fallback vào raw_data cho formatter thấy
    """
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")
    intent = state.get("intent", "unknown")
    student_id = state.get("student_id")
    conversation_id = state.get("conversation_id")
    fallback_reason = state.get("fallback_reason", "timeout")
    tools = _get_tools()
    started = time.perf_counter()

    raw_data: Any = {"message": "No tool mapped", "items": []}
    if intent and intent not in frozenset({"greeting", "thanks", "unknown", None, ""}):
        try:
            async def _call():
                return await tools.call(intent, {
                    "q": seg,
                    "student_id": student_id,
                    "conversation_id": conversation_id,
                })

            raw_data = asyncio.run(_call())
        except Exception as exc:
            err = f"TOOLS_LAYER_UNEXPECTED: {type(exc).__name__}: {exc}"
            print(f"[FALLBACK] tool error: {err}")
            raw_data = {"status": "error", "error": err}

    _metrics.increment("agent.fallback_to_rule")
    _metrics.observe_latency("agent.fallback.latency", time.perf_counter() - started)
    print(f"[FALLBACK] reason={fallback_reason} intent={intent}")

    if isinstance(raw_data, dict):
        fallback_note = (
            "[Lưu ý] Quá trình xử lý mất hơn bình thường, "
            "kết quả dưới đây có thể chưa được lọc theo đầy đủ ràng buộc của bạn. "
            "Bạn vui lòng kiểm tra lại nhé!"
        )
        raw_data["_fallback_note"] = fallback_note
        raw_data["_fallback_reason"] = fallback_reason

    return {
        **state,
        "raw_data": raw_data,
        "used_fallback": True,
        "node_trace": state.get("node_trace", []) + ["rule_based_fallback_node"],
    }
