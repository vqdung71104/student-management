"""
graph_nodes.py — Pure node functions for the LangGraph chatbot pipeline.
Mỗi hàm chỉ trả về MỘT DICT CHỨA CÁC KEY CẦN CẬP NHẬT. Tuyệt đối không return **state.
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

# TĂNG TIMEOUT CHO TOÀN BỘ HỆ THỐNG
INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "64"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "25.0"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "24"))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "25.0"))
NODE4_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "256"))
NODE4_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.1"))
NODE4_GENERATE_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
NODE4_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
NODE4_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "25.0"))
AGENT_REASONING_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))
GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))
AGENT_EXTRACT_MAX_TOKENS = int(os.environ.get("AGENT_EXTRACT_MAX_TOKENS", "128"))
AGENT_FILTER_MAX_TOKENS = int(os.environ.get("AGENT_FILTER_MAX_TOKENS", "256"))

_TRIM_FIELDS = frozenset({
    "_student_course_pk", "_in_student_program", "_student_learning_status",
    "_student_grade_history", "_student_latest_grade", "_student_latest_semester",
    "_student_course_name", "_student_context_message", "_intent_type",
    "_id", "_score", "_rank",
})
_MAX_ITEMS_PER_LIST = 20

_CONSTRAINT_KEYWORDS = frozenset({
    "không muốn", "ngoại trừ", "tránh", "lúc", "thay vì", "không học", "sau", "trước",
})

_GRADUATION_KEYWORDS = frozenset({
    "tín chỉ còn lại", "tín chỉ thiếu", "hoàn thành chương trình", 
    "chương trình đào tạo", "tốt nghiệp", "bao nhiêu tín chỉ",
})

_NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})

_llm_client: Optional[LLMClient] = None
_tools_registry: Optional[ToolsRegistry] = None
_response_cache: Optional[ResponseCache] = None
_tfidf_classifier = TfidfIntentClassifier() if TfidfIntentClassifier else None
_metrics = get_orchestration_metrics()

def _get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None: _llm_client = LLMClient()
    return _llm_client

def _get_tools() -> ToolsRegistry:
    global _tools_registry
    if _tools_registry is None: _tools_registry = ToolsRegistry()
    return _tools_registry

def _get_cache() -> ResponseCache:
    global _response_cache
    if _response_cache is None: _response_cache = ResponseCache()
    return _response_cache

def _is_complex_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _CONSTRAINT_KEYWORDS)

def safe_json_parse(text: str) -> Dict[str, Any]:
    if not text: return {}
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except json.JSONDecodeError: pass
    return {}

def _trim_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _trim_data(v) for k, v in data.items() if k not in _TRIM_FIELDS}
    if isinstance(data, list):
        if len(data) > _MAX_ITEMS_PER_LIST: return _trim_data(data[:_MAX_ITEMS_PER_LIST])
        return [_trim_data(item) for item in data]
    return data

def _compact_data(raw: Any) -> str:
    trimmed = _trim_data(raw)
    if isinstance(trimmed, list):
        lines = []
        for item in trimmed:
            if isinstance(item, dict):
                essential = {k: v for k, v in item.items() if isinstance(v, (str, int, float, bool))}
                lines.append(", ".join([f"{k}={v}" for k, v in essential.items()][:10]))
            else: lines.append(str(item)[:100])
        return "\n".join(lines)[:2000]
    return str(trimmed)[:1000]

def _is_data_empty(data: Any) -> bool:
    if data is None: return True
    if isinstance(data, list) and len(data) == 0: return True
    if isinstance(data, dict):
        if data.get("sql_error"): return True
        if data.get("is_preference_collecting") is True: return False
        keys_check = ["data", "result", "text", "rows", "items", "remaining_subjects", "total_credits_remaining"]
        if any(k in data for k in keys_check):
            for key in keys_check:
                if key in data and data[key] is not None and data[key] != []: return False
        if isinstance(data.get("text"), str) and data["text"].strip(): return False
        if not any(k in data for k in keys_check): return True
    if isinstance(data, str) and not data.strip(): return True
    return False

def _extract_result_data(raw_result: Any) -> Any:
    if raw_result is None: return None
    if isinstance(raw_result, dict):
        if "status" in raw_result and "data" in raw_result: return _extract_result_data(raw_result["data"])
        if "segment" in raw_result or "raw_result" in raw_result: return _extract_result_data(raw_result.get("raw_result", raw_result))
        return raw_result
    if isinstance(raw_result, list):
        if len(raw_result) == 0: return None
        if len(raw_result) == 1: return _extract_result_data(raw_result[0])
        return [_extract_result_data(item) for item in raw_result]
    return raw_result

def _resolve_node3_subtype(intent: Optional[str]) -> Optional[str]:
    _NODE3A_INTENTS = frozenset({"subject_info", "class_info", "grade_view", "learned_subjects_view", "schedule_view", "schedule_info", "student_info", "graduation_progress"})
    _NODE3C_INTENTS = frozenset({"class_registration_suggestion"})
    _NODE3D_INTENTS = frozenset({"modify_schedule"})
    if intent in _NODE3A_INTENTS: return "node3a"
    if intent in _NODE3B_INTENTS: return "node3b"
    if intent in _NODE3C_INTENTS: return "node3c"
    if intent in _NODE3D_INTENTS: return "node3d"
    return None

# ──────────────────────────────────────────────────────────────────────────────
# NODE 1: query_splitter_node
def query_splitter_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    text = state.get("user_text", "")

    if len(text.split()) < 20 and ('?' not in text and ',' not in text and '.' not in text):
        return {"segments": [text], "node_trace": ["query_splitter_node"]}

    llm = _get_llm()
    prompt = (
        "Tách câu hỏi dựa trên các HÀNH ĐỘNG độc lập (thường nối bởi 'sau đó', 'đồng thời', 'và').\n"
        "TUYỆT ĐỐI KHÔNG TÁCH các cụm từ ràng buộc (như: không muốn, tránh, ngoại trừ) ra khỏi hành động của nó.\n"
        "Ví dụ: 'Tôi muốn đăng ký môn, không học môn X, sau đó xem lịch thi'\n"
        "-> [\"Tôi muốn đăng ký môn, không học môn X\", \"sau đó xem lịch thi\"]\n"
        f"Câu hỏi: {text}\n"
        "Trả về JSON: {\"segments\": [\"seg1\", \"seg2\"]}"
    )
    try:
        async def _split():
            return await llm.classify(prompt, timeout=NODE1_TIMEOUT, max_tokens=128, temperature=0.0)
        res = asyncio.run(_split())
        parsed = safe_json_parse(res.get("text", ""))
        segments = parsed.get("segments", [text])
        if not segments: segments = [text]
    except Exception as exc:
        print(f"[NODE1] LLM split failed: {exc}")
        segments = [text]

    return {"segments": segments, "node_trace": ["query_splitter_node"]}

# ──────────────────────────────────────────────────────────────────────────────
# NODE 2: intent_router_node
_CONSTRAINT_REGEX = re.compile(
    r'(?:tôi\s+)?(?:không\s+muốn|tránh|ngoại\s+trừ|không\s+học|thay\s+vì)[^,;\.]*', 
    re.IGNORECASE
)

def _strip_constraints(text: str) -> tuple[str, List[str]]:
    phrases = []
    clean = text
    for match in _CONSTRAINT_REGEX.finditer(clean):
        phrases.append(match.group(0).strip())
    
    for p in phrases:
        clean = clean.replace(p, "")
        
    clean = re.sub(r'\s{2,}', ' ', clean)
    # XÓA SẠCH các từ nối bị lửng lơ ở cuối câu để tránh query rác (LỖI GỐC)
    clean = re.sub(r'[,;\s]+(?:sau\s+đó|đồng\s+thời|rồi|và|tiếp\s+theo)\b[,;\s]*$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^[,;\s]+|[,;\s]+$', '', clean).strip()
    
    return clean if clean else text, phrases

def intent_router_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    segments = state.get("segments", [state.get("user_text", "")])
    idx = state.get("current_segment_index", 0)
    seg = segments[idx] if idx < len(segments) else state.get("user_text", "")

    clean_query, constraint_phrases = _strip_constraints(seg)
    is_complex = bool(constraint_phrases) or _is_complex_query(seg)
    
    constraints = {
        "constraint_phrases": constraint_phrases,
        "exclude_subjects": [], "forbidden_time_slots": [], "forbidden_times": [], "semester": None, "days": []
    }

    if any(kw in seg.lower() for kw in _GRADUATION_KEYWORDS):
        return {"intent": "graduation_progress", "confidence": 0.95, "intent_source": "keyword",
                "is_complex": True, "needs_agent": True, "constraints": constraints, "clean_query": seg,
                "node_trace": ["intent_router_node"]}

    has_reg = any(kw in seg.lower() for kw in ("đăng ký", "đăng kí", "register"))
    if has_reg and is_complex:
        return {"intent": "subject_registration_suggestion", "confidence": 0.95, "intent_source": "bias",
                "is_complex": True, "needs_agent": True, "constraints": constraints, "clean_query": clean_query,
                "node_trace": ["intent_router_node"]}

    intent = "unknown"
    confidence = 0.0
    if _tfidf_classifier and clean_query:
        try:
            async def _classify(): return await _tfidf_classifier.classify_intent(clean_query)
            tfidf_res = asyncio.run(_classify())
            intent = tfidf_res.get("intent", "unknown")
            confidence = float(tfidf_res.get("confidence_score", 0.0))
            if confidence >= INTENT_CONF_THRESHOLD:
                return {"intent": intent, "confidence": confidence, "intent_source": "tfidf",
                        "is_complex": is_complex, "needs_agent": is_complex, "constraints": constraints, 
                        "clean_query": clean_query, "node_trace": ["intent_router_node"]}
        except Exception: pass

    return {"intent": intent, "confidence": confidence, "intent_source": "fallback",
            "is_complex": is_complex, "needs_agent": True, "constraints": constraints,
            "clean_query": clean_query, "node_trace": ["intent_router_node"]}

# ──────────────────────────────────────────────────────────────────────────────
# NODE 3: constraint_parser_node
CONSTRAINT_EXTRACT_PROMPT = (
    "Trích xuất JSON từ câu: {query}\n"
    "Trả về JSON:\n"
    "{{\"exclude_subjects\": [\"mã hoặc tên môn\"], \"forbidden_time_slots\": []}}"
)
def constraint_parser_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    seg = state.get("segments", [""])[state.get("current_segment_index", 0)]
    constraints = state.get("constraints", {})
    
    if constraints.get("constraint_phrases"):
        try:
            llm = _get_llm()
            async def _extract():
                return await llm.classify(CONSTRAINT_EXTRACT_PROMPT.format(query=seg), timeout=10.0, max_tokens=128, temperature=0.0)
            res = asyncio.run(_extract())
            parsed = safe_json_parse(res.get("text", ""))
            if "exclude_subjects" in parsed:
                constraints["exclude_subjects"] = parsed["exclude_subjects"]
        except Exception: pass

    return {"constraints": constraints, "node_trace": ["constraint_parser_node"]}

# ──────────────────────────────────────────────────────────────────────────────
# NODE 4: tool_executor_node
def tool_executor_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    seg = state.get("segments", [""])[state.get("current_segment_index", 0)]
    intent = state.get("intent", "unknown")
    
    raw_data = {"message": "No tool mapped", "items": []}
    needs_agent_filter = (intent in _NODE3B_INTENTS) or bool(state.get("constraints", {}).get("exclude_subjects"))

    if intent not in ("unknown", None, ""):
        try:
            tools = _get_tools()
            async def _call():
                return await tools.call(intent, {
                    "q": state.get("clean_query", seg), "student_id": state.get("student_id"), "conversation_id": state.get("conversation_id")
                })
            raw_data = asyncio.run(_call())
        except Exception as exc:
            raw_data = {"status": "error", "error": str(exc)}

    return {"raw_data": raw_data, "needs_agent_filter": needs_agent_filter, "node_trace": ["tool_executor_node"]}

# ──────────────────────────────────────────────────────────────────────────────
# NODE 5: agent_filter_node
def agent_filter_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    raw_data = state.get("raw_data")
    constraints = state.get("constraints", {})
    excluded = constraints.get("exclude_subjects", [])
    
    filtered_data = raw_data
    
    if excluded and isinstance(raw_data, dict):
        data_list = None
        # Un-wrap FastAPI structure: {"status": "success", "data": {"data": [...]}} or {"data": [...]}
        if "data" in raw_data:
            if isinstance(raw_data["data"], list):
                data_list = raw_data["data"]
            elif isinstance(raw_data["data"], dict) and "data" in raw_data["data"] and isinstance(raw_data["data"]["data"], list):
                data_list = raw_data["data"]["data"]
                
        if data_list is not None:
            new_list = [
                item for item in data_list 
                if not any(exc.lower() in str(item.get("subject_name", "")).lower() for exc in excluded)
            ]
            # Pack it back into original structure
            if isinstance(raw_data["data"], list):
                raw_data["data"] = new_list
            else:
                raw_data["data"]["data"] = new_list
            filtered_data = raw_data

    return {"filtered_data": filtered_data, "node_trace": ["agent_filter_node"]}

# ──────────────────────────────────────────────────────────────────────────────
# NODE 6: response_formatter_node
def response_formatter_node(state: AgentState) -> Dict[str, Any]:
    started = time.perf_counter()
    raw = state.get("filtered_data") or state.get("raw_data")
    seg = state.get("segments", [""])[state.get("current_segment_index", 0)]
    
    text = "Mình đã xử lý xong yêu cầu của bạn."
    if _is_data_empty(raw):
        text = "Rất tiếc, mình không tìm thấy thông tin phù hợp với yêu cầu của bạn."
    else:
        try:
            llm = _get_llm()
            prompt = f"Dữ liệu: {json.dumps(_extract_result_data(raw), ensure_ascii=False)[:1000]}\nCâu hỏi: {seg}\nHãy trả lời tiếng Việt ngắn gọn."
            async def _gen(): return await llm.generate(prompt, timeout=15.0, max_tokens=256)
            res = asyncio.run(_gen())
            text = res.get("text", text)
        except Exception:
            text = "Dữ liệu đã được lấy nhưng mình gặp lỗi khi trình bày."

    return {
        "final_response": text,
        "formatted_result": {"text": text, "from_cache": False, "model_used": "openai", "processing_time_ms": 0},
        "node_trace": ["response_formatter_node"]
    }

# ──────────────────────────────────────────────────────────────────────────────
# ACCUMULATE NODE
def _accumulate_and_route_node(state: AgentState) -> Dict[str, Any]:
    idx = state.get("current_segment_index", 0)
    final_raw = state.get("filtered_data") or state.get("raw_data")
    seg = state.get("segments", [""])[idx]
    
    seg_result = {
        "segment": seg,
        "intent": {"intent": state.get("intent"), "confidence": state.get("confidence")},
        "raw_result": final_raw,
        "node3_subtype": _resolve_node3_subtype(state.get("intent")),
        "route": "agent" if state.get("needs_agent") else "rule_based",
    }
    
    return {
        "segment_results": [seg_result], # Sử dụng List cho toán tử operator.add
        "current_segment_index": idx + 1,
        # CLEAR trạng thái cho segment tiếp theo
        "raw_data": None, 
        "filtered_data": None, 
        "intent": None,
        "clean_query": None,
        "constraints": None,
        "node_trace": ["_accumulate_and_route_node"]
    }

# ──────────────────────────────────────────────────────────────────────────────
# NODE 7: synthesize_formatter_node
def synthesize_formatter_node(state: AgentState) -> Dict[str, Any]:
    """
    Sử dụng LLM tổng hợp toàn bộ kết quả segment thay vì placeholder "Đã tổng hợp".
    """
    segment_results = state.get("segment_results", [])
    user_text = state.get("user_text", "")
    
    # Nếu chỉ có 1 câu hỏi, bỏ qua bước tổng hợp
    if len(segment_results) < 2:
        return {"node_trace": ["synthesize_formatter_node"]}
        
    lines = []
    for i, res in enumerate(segment_results, 1):
        seg_text = res.get("segment", "")
        intent_val = res.get("intent", {}).get("intent", "unknown")
        raw = res.get("raw_result")
        
        extracted = _extract_result_data(raw)
        res_text = str(extracted)[:600] if extracted else "Không có dữ liệu"
        lines.append(f"--- Yêu cầu {i} ---\nCâu hỏi: {seg_text}\nKết quả hệ thống: {res_text}\n")
    
    context = "\n".join(lines)
    prompt = (
        "Bạn là trợ lý học vụ. Tổng hợp các kết quả từ nhiều câu hỏi thành MỘT câu trả lời duy nhất, tự nhiên, và chuyên nghiệp.\n"
        "YÊU CẦU QUAN TRỌNG:\n"
        "1. Trả lời bao quát TẤT CẢ các câu hỏi theo ĐÚNG THỨ TỰ.\n"
        "2. Cung cấp thông tin thực sự chi tiết từ mục 'Kết quả hệ thống'. Đừng nói chung chung.\n"
        "3. Nếu yêu cầu nào không tìm thấy dữ liệu, hãy thông báo rõ ràng.\n\n"
        f"Câu hỏi gốc: {user_text}\n\n"
        f"Kết quả từng phần:\n{context}\n\n"
        "Câu trả lời tổng hợp:"
    )
    
    try:
        llm = _get_llm()
        async def _gen(): return await llm.generate(prompt, timeout=20.0, max_tokens=512)
        res = asyncio.run(_gen())
        text = res.get("text", "Đã xử lý xong các yêu cầu của bạn.")
    except Exception as exc:
        print(f"[SYNTHESIZE] Error: {exc}")
        text = "Mình đã tìm được thông tin nhưng gặp chút lỗi khi tổng hợp, bạn xem chi tiết phía trên nhé."
        
    return {
        "synthesized_response": text,
        "final_response": text,  # Đè lên final_response để màn hình hiển thị text này
        "node_trace": ["synthesize_formatter_node"]
    }

# ──────────────────────────────────────────────────────────────────────────────
# NODE 8: rule_based_fallback_node
def rule_based_fallback_node(state: AgentState) -> Dict[str, Any]:
    return {"used_fallback": True, "node_trace": ["rule_based_fallback_node"]}