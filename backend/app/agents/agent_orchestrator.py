import asyncio
import hashlib
import json
import os
import re
import time
import traceback
import unicodedata
from typing import Any, Dict, FrozenSet, List, Optional

from app.llm.llm_client import LLMClient
from app.llm.llm_client import LLMCircuitOpenError, LLMAPIError, LLMTimeoutError
from app.llm.response_cache import ResponseCache
from .graph_nodes import format_rule_based_response, join_rule_based_segments
from .orchestration_metrics import get_orchestration_metrics
from .tools_registry import ToolsRegistry

INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "48"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "12"))
NODE4_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "150"))
NODE4_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.1"))
NODE4_GENERATE_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
NODE4_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "3.0"))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2.0"))
NODE4_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "25.0"))
LLM_REASONING_TIMEOUT = float(os.environ.get("LLM_REASONING_TIMEOUT", "5.0"))
TOOL_EXECUTION_TIMEOUT = float(os.environ.get("TOOL_EXECUTION_TIMEOUT", "10.0"))
AGENT_REASONING_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))
AGENT_EXTRACT_MAX_TOKENS = int(os.environ.get("AGENT_EXTRACT_MAX_TOKENS", "64"))
AGENT_FILTER_MAX_TOKENS = int(os.environ.get("AGENT_FILTER_MAX_TOKENS", "128"))
OPENAI_GENERATE_TIMEOUT = float(os.environ.get("OPENAI_GENERATE_TIMEOUT", "25.0"))

# LangGraph integration mode
HANDLE_MODE = os.environ.get("AGENT_HANDLE_MODE", "graph").lower()

try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None

# Fields to REMOVE from data before sending to Node 4
_TRIM_FIELDS = frozenset({
    "_student_course_pk", "_in_student_program", "_student_learning_status",
    "_student_grade_history", "_student_latest_grade", "_student_latest_semester",
    "_student_course_name", "_student_context_message", "_intent_type",
    "_id", "_score", "_rank",
})
_MAX_ITEMS_PER_LIST = 20

# Multi-intent connectors
_MULTI_INTENT_PATTERNS = frozenset({
    " sau đó ", " sau đó,", "đồng thời", " và ", " rồi ", " tiếp theo ",
    " vừa ", " luôn ",
})

# Constraint keywords
_CONSTRAINT_KEYWORDS = frozenset({
    "không muốn", "ngoại trừ", "tránh", "lúc", "thay vì",
    "không học", "sau", "trước",
})

# Constraint phrase patterns (for stripping)
_CONSTRAINT_PREFIX_PATTERNS = [
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
    re.compile(r'(tránh\s+(?:môn|học phần|lớp)\s*\S[^\.,;]*)', re.IGNORECASE),
    re.compile(r'(ngoại\s+trừ\s+(?:môn|học phần)\s*\S[^\.,;]*)', re.IGNORECASE),
]

# Node-3 subtype constants
_NODE3A_INTENTS = frozenset({
    "subject_info", "class_info", "grade_view",
    "learned_subjects_view", "schedule_view", "schedule_info", "student_info",
    "graduation_progress",
})
_NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})
_NODE3C_INTENTS = frozenset({"class_registration_suggestion"})
_NODE3D_INTENTS = frozenset({"modify_schedule"})


def _strip_constraints(text: str) -> tuple[str, List[str]]:
    """
    Trích xuất các cụm từ ràng buộc khỏi câu query.
    Trả về (clean_query, constraint_phrases).
    """
    constraint_phrases: List[str] = []
    clean = text

    for pattern in _CONSTRAINT_PREFIX_PATTERNS:
        for match in pattern.finditer(clean):
            phrase = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if phrase and len(phrase) > 2 and phrase.lower() not in (
                "và", "sau", "trước", "tránh", "ngoại trừ", "thay vì"
            ):
                constraint_phrases.append(phrase)

    for phrase in constraint_phrases:
        clean = re.sub(re.escape(phrase), '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s{2,}', ' ', clean)
        clean = re.sub(r'[,;]\s*[,;]', ',', clean)

    clean = clean.strip()
    clean = re.sub(r'[,;]\s*$', '', clean).strip()
    if not clean:
        clean = text
    return clean, constraint_phrases


def _safe_json_parse(text: str) -> Dict[str, Any]:
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


def _normalize_text(text: str) -> str:
    normalized = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return normalized.lower()


class AgentOrchestrator:
    def __init__(self, llm_client: Optional[LLMClient] = None, tools: Optional[ToolsRegistry] = None, cache: Optional[ResponseCache] = None):
        self.llm = llm_client or LLMClient()
        self.tools = tools or ToolsRegistry()
        self.cache = cache or ResponseCache()
        self.tfidf = TfidfIntentClassifier() if TfidfIntentClassifier else None
        self.metrics = get_orchestration_metrics()

    def _stable_payload(self, value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except TypeError:
            return str(value)

    def _hash_raw_result(self, raw: Any, instruction: str) -> str:
        raw_bytes = self._stable_payload({"instruction": instruction, "raw": raw}).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def _trim_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._trim_data(v) for k, v in data.items() if k not in _TRIM_FIELDS}
        if isinstance(data, list):
            if len(data) > _MAX_ITEMS_PER_LIST:
                return self._trim_data(data[:_MAX_ITEMS_PER_LIST])
            return [self._trim_data(item) for item in data]
        return data

    def _is_data_empty(self, data: Any) -> bool:
        if data is None:
            return True
        if isinstance(data, list) and len(data) == 0:
            return True
        if isinstance(data, dict):
            if data.get("sql_error"):
                return True
            if data.get("is_preference_collecting") is True:
                return False
            keys_that_matter = ["data", "result", "text", "rows", "items"]
            for key in keys_that_matter:
                if key in data:
                    val = data[key]
                    if val is not None and not (isinstance(val, list) and len(val) == 0):
                        return False
            text_val = data.get("text")
            if isinstance(text_val, str) and text_val.strip():
                return False
            if not any(k in data for k in keys_that_matter):
                return True
        if isinstance(data, str) and not data.strip():
            return True
        return False

    def _extract_result_data(self, raw_result: Any) -> Any:
        if raw_result is None:
            return None
        if isinstance(raw_result, dict):
            if "status" in raw_result and "data" in raw_result:
                return self._extract_result_data(raw_result["data"])
            if "segment" in raw_result or "raw_result" in raw_result:
                return self._extract_result_data(raw_result.get("raw_result", raw_result))
            text_val = raw_result.get("text")
            if isinstance(text_val, str) and text_val.strip():
                return raw_result
            return raw_result
        if isinstance(raw_result, list):
            if len(raw_result) == 0:
                return None
            if len(raw_result) == 1:
                return self._extract_result_data(raw_result[0])
            return [self._extract_result_data(item) for item in raw_result]
        return raw_result

    def _compact_data(self, raw: Any) -> str:
        trimmed = self._trim_data(raw)
        if isinstance(trimmed, list):
            lines = []
            for item in trimmed:
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

    def _build_formatter_prompt(
        self,
        raw_result: Any,
        instruction: str,
        original_query: Optional[str] = None,
        intent_hints: Optional[List[str]] = None,
    ) -> str:
        extracted = self._extract_result_data(raw_result)
        try:
            json_data = json.dumps(extracted, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            json_data = str(extracted) if extracted is not None else "{}"

        prompt_parts = []
        prompt_parts.append(f"Dữ liệu hệ thống trả về: {json_data}")
        prompt_parts.append(f"Câu hỏi người dùng: {original_query or instruction}")
        if intent_hints:
            intents_str = ", ".join(str(i) for i in intent_hints if i)
            prompt_parts.append(f"Intent (ngữ cảnh xử lý): {intents_str}")
        prompt_parts.append("")
        prompt_parts.append("Hãy trả lời bằng tiếng Việt, ngắn gọn, chuyên nghiệp theo phong cách trợ lý học vụ.")
        return "\n".join(prompt_parts)

    def _normalize_confidence(self, value: Any) -> float:
        try:
            c = float(value)
        except Exception:
            return 0.0
        return max(0.0, min(1.0, c))

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.5:
            return "medium"
        return "low"

    def _is_complex_query(self, text: str) -> bool:
        lower = _normalize_text(text)
        return any(kw in lower for kw in _CONSTRAINT_KEYWORDS)

    def _resolve_node3_subtype(self, intent: Optional[str]) -> Optional[str]:
        if intent in _NODE3A_INTENTS:
            return "node3a"
        if intent in _NODE3B_INTENTS:
            return "node3b"
        if intent in _NODE3C_INTENTS:
            return "node3c"
        if intent in _NODE3D_INTENTS:
            return "node3d"
        return None

    def _preview(self, value: Any, max_len: int = 140) -> str:
        text = self._stable_payload(value)
        return text if len(text) <= max_len else text[:max_len] + "..."

    # ── Agent reasoning prompts ───────────────────────────────────────────────
    _AGENT_FILTER_PROMPT = (
        "Bạn là trợ lý học vụ. Lọc danh sách theo ràng buộc của sinh viên.\n"
        "Ràng buộc: {constraints}\n"
        "Dữ liệu thô: {data}\n\n"
        "Quy tắc:\n"
        "  - Loại bỏ các mục vi phạm ràng buộc (VD: exclude_subjects, forbidden_time_slots...)\n"
        "Trả về JSON: {{'status': 'success', 'data': <danh_sách_đã_lọc>}}\n"
        "Nếu tất cả bị loại, trả về: {{'status': 'success', 'data': []}}"
    )

    # ── Node 1: Query Splitter (multi-intent + constraint guard) ───────────────
    async def node1_query_splitter(self, text: str) -> List[str]:
        started_at = time.perf_counter()

        # Guard: never split if constraints present
        if self._is_complex_query(text):
            self.metrics.increment("node1.constraint_guard_hit")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] constraint_guard → 1 segment")
            return [text]

        # Trivial case
        if len(text.split()) < 40 and ('?' not in text and ',' not in text and '.' not in text):
            self.metrics.increment("node1.heuristic_hit")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            return [text]

        # Multi-intent connectors: 'sau đó', 'đồng thời', 'và', 'rồi', 'tiếp theo'
        _SPLIT_PATTERN = re.compile(
            r'(?<=[,;])\s*(?:sau đó|đồng thời|rồi|tiếp theo)\b|'
            r'\s+(?:sau đó|đồng thời)\s+|'
            r'\s+và\s+|'
            r'\s+vừa\s+',
            re.IGNORECASE,
        )
        if _SPLIT_PATTERN.search(text):
            parts = _SPLIT_PATTERN.split(text)
            segments = [p.strip() for p in parts if p.strip()]
            if len(segments) >= 2:
                self.metrics.increment("node1.multi_intent_split")
                duration = time.perf_counter() - started_at
                self.metrics.observe_latency("node1.latency", duration)
                print(f"[NODE-1:SPLIT] multi_intent → {len(segments)} segments")
                return segments

        # LLM split fallback
        try:
            res = await self.llm.split(text, timeout=NODE1_TIMEOUT,
                                       max_tokens=NODE1_SPLIT_MAX_TOKENS, temperature=0.0)
            segments = res.get('segments') or [text]
            self.metrics.increment("node1.llm_success")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] LLM → {len(segments)} segments")
            return segments
        except Exception as exc:
            self.metrics.increment("node1.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            fallback_segments = [s.strip() for s in text.replace('?', '.').split('.') if s.strip()]
            print(f"[NODE-1:SPLIT] fallback: {exc} → {len(fallback_segments)} segments")
            return fallback_segments or [text]

    # ── Node 2: Intent Router (CONSTRAINT STRIPPING + TF-IDF on clean_query) ──
    async def node2_intent_router(self, text: str) -> Dict[str, Any]:
        """
        Yêu cầu kỹ thuật — CONSTRAINT STRIPPING:
          1. Trước khi gọi TF-IDF, trích xuất constraint phrases (sau 'không muốn', 'tránh', 'ngoại trừ').
          2. Cắt bỏ chúng → clean_query.
          3. TF-IDF chạy trên clean_query.
          4. Lưu constraint_phrases vào state['constraints'].

        Ví dụ:
          'Tôi muốn đăng ký học phần, tránh môn X'
          → clean_query = 'Tôi muốn đăng ký học phần'
          → Intent = subject_registration_suggestion (from clean_query)
          → Constraints: exclude_subjects = ['X']
        """
        started_at = time.perf_counter()
        is_complex = self._is_complex_query(text)

        # ── Step 1: Constraint Stripping ─────────────────────────────────────
        clean_query, constraint_phrases = _strip_constraints(text)
        constraints: Dict[str, Any] = {
            "constraint_phrases": constraint_phrases,
            "exclude_subjects": [],
            "forbidden_time_slots": [],
            "forbidden_times": [],
            "semester": None,
            "days": [],
        }

        # Parse exclude_subjects from constraint_phrases
        if constraint_phrases:
            try:
                phrases_str = ", ".join(f'"{p}"' for p in constraint_phrases)
                prompt = (
                    f"Bạn là trợ lý học vụ. Trích xuất danh sách mã môn học từ các cụm từ sau.\n"
                    f"Cụm từ: [{phrases_str}]\n\n"
                    f"Trả về JSON thuần: {{'exclude_subjects': ['IT1111', ...]}}\n"
                    f"Nếu không có mã môn nào: {{'exclude_subjects': []}}"
                )
                res = await self.llm.generate(prompt, timeout=5.0, max_tokens=64, temperature=0.0)
                parsed = _safe_json_parse(res.get("text", "{}"))
                if isinstance(parsed, dict) and "exclude_subjects" in parsed:
                    constraints["exclude_subjects"] = parsed["exclude_subjects"]
            except Exception as exc:
                print(f"[NODE-2] constraint parse: {exc}")

        print(f"[NODE-2:ROUTE] strip → clean_query={self._preview(clean_query, 80)} "
              f"constraints={constraint_phrases}")

        # ── Step 2: TF-IDF on clean_query ─────────────────────────────────────
        label = 'unknown'
        score = 0.0

        if self.tfidf and clean_query:
            try:
                tfidf_res = await self.tfidf.classify_intent(clean_query)
                label = tfidf_res.get("intent", "unknown")
                score = tfidf_res.get("confidence_score", 0.0)
                if score >= INTENT_CONF_THRESHOLD or len(clean_query.split()) <= 20:
                    needs_agent = is_complex
                    self.metrics.increment("node2.tfidf_hit")
                    duration = time.perf_counter() - started_at
                    self.metrics.observe_latency("node2.latency", duration)
                    print(f"[NODE-2:ROUTE] TF-IDF → intent={label} conf={score:.3f} "
                          f"needs_agent={needs_agent}")
                    return {
                        "intent": label,
                        "confidence": score,
                        "source": "tfidf",
                        "needs_agent": needs_agent,
                        "is_complex": is_complex,
                        "constraints": constraints,
                        "clean_query": clean_query,
                    }
            except Exception as exc:
                print(f"[NODE-2] TF-IDF failed: {exc}")

        # ── Step 3: LLM fallback on clean_query ──────────────────────────────
        try:
            llm_res = await self.llm.classify(
                clean_query,
                timeout=NODE2_TIMEOUT,
                max_tokens=NODE2_CLASSIFY_MAX_TOKENS,
                temperature=0.0,
            )
            intent = llm_res.get('intent') or llm_res.get('label') or "unknown"
            confidence = self._normalize_confidence(llm_res.get('confidence', 0.0))
            self.metrics.increment("node2.llm_success")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node2.latency", duration)
            print(f"[NODE-2:ROUTE] LLM → intent={intent} conf={confidence:.3f}")
            return {
                "intent": intent,
                "confidence": confidence,
                "source": "llm",
                "needs_agent": True,
                "is_complex": is_complex,
                "constraints": constraints,
                "clean_query": clean_query,
            }
        except Exception as exc:
            self.metrics.increment("node2.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node2.latency", duration)
            fallback_intent = label if self.tfidf else 'unknown'
            fallback_score = score if self.tfidf else 0.0
            print(f"[NODE-2:ROUTE] fallback: {exc}")
            return {
                "intent": fallback_intent,
                "confidence": fallback_score,
                "source": "fallback",
                "needs_agent": True,
                "is_complex": is_complex,
                "constraints": constraints,
                "clean_query": clean_query,
            }

    # ── Node 4: Response Formatter (synthesizes segment_results) ─────────────
    async def node4_response_formatter(
        self,
        raw_result: Any,
        instruction: str,
        original_query: Optional[str] = None,
        intent_hints: Optional[List[str]] = None,
        segment_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Node 4: Format raw data into friendly response.
        - Anti-hallucination: if data is empty/error, return fallback message.
        - Multi-segment: if segment_results has >= 2 items, LLM synthesizes a
          single natural response covering ALL requests in order.
        - OpenAI GPT-4o-mini primary, 15s timeout → rulebase fallback.
        """
        started_at = time.perf_counter()
        llm_processing_time_ms = 0.0
        model_used = "none"
        seg_results = segment_results or []

        # ── Multi-segment synthesis ─────────────────────────────────────────────
        if len(seg_results) >= 2:
            return await self._synthesize_multi_segment(
                seg_results, original_query or instruction, started_at
            )

        # ── Single segment: existing logic ─────────────────────────────────────
        extracted_data = self._extract_result_data(raw_result)

        # Handle error status
        if isinstance(raw_result, dict) and raw_result.get("status") == "error":
            error_msg = raw_result.get("error") or "Unknown tool error"
            print(f"[NODE-4:ERROR] {error_msg}")
            self.metrics.increment("node4.tool_error_status")
            total_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4.latency", total_ms / 1000)
            return {
                "text": "Mình gặp một chút trục trặc khi xử lý yêu cầu này. "
                        "Bạn vui lòng thử lại hoặc diễn đạt câu hỏi theo cách khác nhé!",
                "from_cache": False,
                "processing_time_ms": 0.0,
                "model_used": "error_status",
            }

        # Passive mode for subject_registration_suggestion
        is_passive = (
            isinstance(extracted_data, dict)
            and extracted_data.get("preformatted_text")
            and extracted_data.get("text")
            and (intent_hints is None or "subject_registration_suggestion" in intent_hints)
        )
        if is_passive:
            raw_text = extracted_data.get("text") or extracted_data.get("preformatted_text") or ""
            total_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.increment("node4.passive_pass_through")
            self.metrics.observe_latency("node4.latency", total_ms / 1000)
            return {
                "text": raw_text,
                "from_cache": False,
                "processing_time_ms": 0.0,
                "model_used": "passive_pass_through",
                "passive_mode": True,
            }

        # Anti-hallucination guard
        if self._is_data_empty(extracted_data):
            print("[NODE-4:ANTI-HALLU] Data is empty")
            self.metrics.increment("node4.empty_data")
            total_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4.latency", total_ms / 1000)
            return {
                "text": "Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. "
                        "Bạn vui lòng kiểm tra lại nhé!",
                "from_cache": False,
                "processing_time_ms": 0.0,
                "model_used": "none",
                "empty_data_guard": True,
            }

        # Original query from results
        if original_query is None:
            if isinstance(raw_result, list) and len(raw_result) > 0:
                original_query = raw_result[0].get("segment", instruction)
            elif isinstance(raw_result, dict):
                original_query = raw_result.get("segment", instruction)
            else:
                original_query = instruction

        # Cache check
        cache_key_data = extracted_data
        h = self._hash_raw_result(cache_key_data, instruction)
        cached = self.cache.get(h)
        if cached:
            self.metrics.increment("node4.cache_hit")
            total_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4.latency", total_ms / 1000)
            return {"text": cached, "from_cache": True, "processing_time_ms": 0, "model_used": "cache"}

        self.metrics.increment("node4.cache_miss")

        # Build prompt
        prompt = self._build_formatter_prompt(
            extracted_data, instruction, original_query, intent_hints=intent_hints
        )

        _FEW_SHOT = """
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
"""
        prompt = prompt + "\n" + _FEW_SHOT

        # Call LLM
        try:
            gen_started = time.perf_counter()
            gen = await self.llm.generate(
                prompt,
                max_tokens=NODE4_GENERATE_MAX_TOKENS,
                temperature=NODE4_GENERATE_TEMPERATURE,
                timeout=NODE4_TIMEOUT,
                top_p=NODE4_GENERATE_TOP_P,
                repeat_penalty=NODE4_REPEAT_PENALTY,
            )
            llm_processing_time_ms = (time.perf_counter() - gen_started) * 1000
            text = (gen.get('text') or str(gen) or "").strip()
            model_used = gen.get('model_used', 'openai')
            if not text:
                raise ValueError("LLM returned empty text")
            self.metrics.increment("node4.llm_success")
        except LLMCircuitOpenError:
            self.metrics.increment("node4.circuit_open")
            text = "Hệ thống đang bận, bạn vui lòng thử lại trong giây lát nhé!"
            model_used = "circuit_open"
        except LLMTimeoutError as exc:
            self.metrics.increment("node4.timeout")
            print(f"[NODE-4:ERROR] LLM timeout after {NODE4_TIMEOUT}s: {exc}")
            text = "Mình đang xử lý hơi chậm, bạn vui lòng thử lại trong giây lát nhé!"
            model_used = "timeout"
        except LLMAPIError as exc:
            self.metrics.increment("node4.api_error")
            print(f"[NODE-4:ERROR] LLM API error: {exc}")
            text = "Mình gặp chút trục trặc khi xử lý câu trả lời, bạn vui lòng thử lại nhé!"
            model_used = "api_error"
        except Exception as exc:
            self.metrics.increment("node4.fallback")
            print(f"[NODE-4:ERROR] Unexpected: {exc}\n{traceback.format_exc()}")
            text = "Mình gặp chút trục trặc khi xử lý câu trả lời, bạn vui lòng thử lại nhé!"
            model_used = "error"
            llm_processing_time_ms = 0

        # Cache result
        self.cache.set(h, text)

        total_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.observe_latency("node4.latency", total_ms / 1000)
        print(f"[NODE-4:DONE] duration={total_ms:.1f}ms LLM={llm_processing_time_ms:.1f}ms model={model_used}")
        return {
            "text": text,
            "from_cache": False,
            "processing_time_ms": llm_processing_time_ms,
            "model_used": model_used,
        }

    async def _synthesize_multi_segment(
        self,
        segment_results: List[Dict[str, Any]],
        original_query: str,
        started_at: float,
    ) -> Dict[str, Any]:
        """
        LLM tổng hợp kết quả từ TẤT CẢ các segment trong segment_results
        thành MỘT câu trả lời duy nhất, tự nhiên, bao quát toàn bộ yêu cầu theo đúng thứ tự.
        """
        lines = []
        for i, seg_result in enumerate(segment_results, start=1):
            seg_text = seg_result.get("segment", "")
            raw = seg_result.get("raw_result")
            intent_label = "unknown"
            intent_info = seg_result.get("intent")
            if isinstance(intent_info, dict):
                intent_label = intent_info.get("intent", "unknown")
            elif intent_info:
                intent_label = str(intent_info)

            if isinstance(raw, dict):
                if raw.get("status") == "error":
                    res_text = f"[Lỗi: {raw.get('error', 'unknown')}]"
                elif raw.get("text") and raw.get("is_preference_collecting"):
                    res_text = raw.get("text", "")
                else:
                    extracted = self._extract_result_data(raw)
                    try:
                        res_text = json.dumps(extracted, ensure_ascii=False, default=str)[:500]
                    except Exception:
                        res_text = str(extracted)[:500] if extracted else ""
            elif isinstance(raw, list):
                res_text = f"[{len(raw)} kết quả]"
            else:
                res_text = str(raw)[:500] if raw else ""

            lines.append(f"--- Câu hỏi {i} ---")
            lines.append(f"Câu hỏi: {seg_text}")
            lines.append(f"Intent: {intent_label}")
            lines.append(f"Kết quả: {res_text}")
            lines.append("")

        segments_context = "\n".join(lines)
        synthesis_prompt = (
            "Bạn là trợ lý học vụ. Tổng hợp các kết quả từ nhiều câu hỏi thành MỘT câu trả lời "
            "duy nhất, tự nhiên, ngắn gọn, chuyên nghiệp.\n\n"
            "YÊU CẦU:\n"
            "  1. Trả lời bao quát TẤT CẢ các câu hỏi theo ĐÚNG THỨ TỰ người dùng hỏi.\n"
            "  2. Dùng tiếng Việt, phong cách trợ lý học vụ.\n"
            "  3. Không lặp lại thông tin, không thừa, không thiếu.\n"
            "  4. Nếu có câu hỏi không tìm thấy kết quả, nói rõ và chuyển sang câu tiếp.\n"
            "  5. Nếu câu hỏi thứ 2 phụ thuộc kết quả câu 1 (VD: 'sau đó'), đảm bảo logic.\n\n"
            f"Câu hỏi gốc: {original_query}\n\n"
            f"Kết quả từng phần:\n{segments_context}\n\n"
            "Trả lời:"
        )

        # Cache check
        cache_key = f"synthesize_{len(segment_results)}_{hash(segments_context) % 10**8}"
        cached = self.cache.get(cache_key)
        if cached:
            self.metrics.increment("node4_synthesize.cache_hit")
            total_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4_synthesize.latency", total_ms / 1000)
            return {
                "text": cached, "from_cache": True, "processing_time_ms": 0,
                "model_used": "cache", "synthesized": True,
            }

        self.metrics.increment("node4_synthesize.cache_miss")
        text = ""
        model_used = "none"
        llm_ms = 0.0

        try:
            gen_started = time.perf_counter()
            res = await self.llm.generate(
                synthesis_prompt,
                max_tokens=NODE4_GENERATE_MAX_TOKENS * 2,
                temperature=NODE4_GENERATE_TEMPERATURE,
                timeout=NODE4_TIMEOUT,
                top_p=NODE4_GENERATE_TOP_P,
                repeat_penalty=NODE4_REPEAT_PENALTY,
            )
            text = (res.get("text") or str(res) or "").strip()
            model_used = res.get("model_used", "openai")
            llm_ms = (time.perf_counter() - gen_started) * 1000
            if text:
                self.cache.set(cache_key, text)
            self.metrics.increment("node4_synthesize.llm_success")
        except Exception as exc:
            self.metrics.increment("node4_synthesize.error")
            print(f"[SYNTHESIZE] error: {exc}\n{traceback.format_exc()}")
            text = "Mình gặp chút trục trặc khi tổng hợp kết quả, bạn vui lòng thử lại nhé!"
            model_used = "error"
            llm_ms = 0

        total_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.observe_latency("node4_synthesize.latency", total_ms / 1000)
        print(f"[SYNTHESIZE] {len(segment_results)} segments → {len(text)} chars model={model_used}")
        return {
            "text": text,
            "from_cache": False,
            "processing_time_ms": llm_ms,
            "model_used": model_used,
            "synthesized": True,
        }

    # ── Agent Filter (LLM-based constraint filtering) ──────────────────────────
    async def _agent_filter(
        self,
        raw_data: Any,
        constraints: Dict[str, Any],
        seg: str,
    ) -> Any:
        """
        LLM lọc raw_data theo constraints.
        """
        has_constraints = any(
            constraints.get(k)
            for k in ("exclude_subjects", "forbidden_time_slots", "forbidden_times", "days")
            if constraints.get(k)
        )
        if not has_constraints:
            return raw_data

        try:
            compact = self._compact_data(raw_data)
            prompt = self._AGENT_FILTER_PROMPT.format(
                constraints=json.dumps(constraints, ensure_ascii=False),
                data=compact,
            )
            res = await self.llm.generate(
                prompt,
                timeout=AGENT_REASONING_TIMEOUT / 2,
                max_tokens=AGENT_FILTER_MAX_TOKENS,
                temperature=0.1,
            )
            parsed = _safe_json_parse(res.get("text", "{}"))
            return parsed if isinstance(parsed, dict) else raw_data
        except Exception as exc:
            print(f"[AGENT_FILTER] failed: {exc}")
            return raw_data

    # ── handle() entry point ─────────────────────────────────────────────────
    async def handle(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Entry point — LangGraph mode.
        """
        if HANDLE_MODE == "graph":
            return await self._handle_graph(user_text, student_id, conversation_id)
        else:
            return await self._handle_linear(user_text, student_id, conversation_id)

    async def _handle_graph(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """LangGraph pipeline entry point."""
        from app.agents.agent_graph import run_graph_for_orchestrator
        try:
            result = await asyncio.wait_for(
                run_graph_for_orchestrator(user_text, student_id, conversation_id),
                timeout=AGENT_REASONING_TIMEOUT,
            )
            return result
        except asyncio.TimeoutError:
            print("[ORCH:GRAPH] LangGraph timeout → falling back to direct node3 pipeline")
            self.metrics.increment("agent.graph_timeout_fallback")
            return await self._handle_direct_node3_fallback(user_text, student_id, conversation_id)
        except Exception as exc:
            print(f"[ORCH:GRAPH] LangGraph error: {exc} → falling back to direct node3 pipeline")
            self.metrics.increment("agent.graph_error_fallback")
            return await self._handle_direct_node3_fallback(user_text, student_id, conversation_id)

    async def _handle_direct_node3_fallback(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        segments = await self.node1_query_splitter(user_text)
        results: List[Dict[str, Any]] = []

        for seg in segments:
            intent_info = await self.node2_intent_router(seg)
            intent = intent_info.get("intent")
            constraints = intent_info.get("constraints", {})
            clean_query = intent_info.get("clean_query", seg)
            node3_subtype = self._resolve_node3_subtype(intent)

            raw_result: Any = {"status": "error", "error": "No tool mapped"}
            if intent not in ("unknown", None, ""):
                try:
                    raw_result = await self.tools.call(
                        intent,
                        {
                            "q": clean_query,
                            "student_id": student_id,
                            "conversation_id": conversation_id,
                        },
                    )
                    if intent == "subject_registration_suggestion":
                        raw_result = await self._agent_filter(raw_result, constraints, seg)
                except Exception as exc:
                    raw_result = {"status": "error", "error": str(exc)}

            results.append(
                {
                    "segment": seg,
                    "intent": intent_info,
                    "raw_result": raw_result,
                    "node3_subtype": node3_subtype,
                    "clean_query": clean_query,
                    "constraints": constraints,
                }
            )

        node4_result = await self.node4_response_formatter(
            results,
            "Generate response",
            original_query=user_text,
            intent_hints=[r.get("intent", {}).get("intent") for r in results if r.get("intent")],
            segment_results=results,
        )
        formatted = node4_result["text"]

        if len(results) > 1:
            summary_intent = "compound"
            confidence_label = "medium"
            confidence_score = 0.6
            is_compound = True
        elif results:
            first = results[0].get("intent") or {}
            summary_intent = first.get("intent", "unknown") if isinstance(first, dict) else "unknown"
            confidence_score = self._normalize_confidence(first.get("confidence", 0.0)) if isinstance(first, dict) else 0.0
            confidence_label = self._confidence_label(confidence_score)
            is_compound = False
        else:
            summary_intent = "unknown"
            confidence_label = "low"
            confidence_score = 0.0
            is_compound = False

        total_ms = (time.perf_counter() - started_at) * 1000
        print(f"[ORCH:FALLBACK] direct_node3 intent={summary_intent} segments={len(results)} duration={total_ms:.1f}ms")
        return {
            "raw": results,
            "response": formatted,
            "text": formatted,
            "intent": summary_intent,
            "confidence": confidence_label,
            "confidence_score": confidence_score,
            "is_compound": is_compound,
            "parts": [
                {
                    "intent": item.get("intent"),
                    "node3_subtype": item.get("node3_subtype"),
                    "text": item.get("segment"),
                    "data": item.get("raw_result"),
                }
                for item in results
            ],
            "debug": {
                "fallback_mode": "direct_node3",
                "llm_processing_time_ms": node4_result.get("processing_time_ms"),
                "model_used": node4_result.get("model_used"),
                "from_cache": node4_result.get("from_cache", False),
            },
        }

    async def _handle_linear(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Legacy sequential hybrid pipeline.
        Updated with:
          - Multi-intent split on 'sau đó', 'đồng thời'
          - Constraint stripping before TF-IDF
          - subject_registration → agent_filter
          - segment_results accumulation
          - Multi-segment synthesis in Node 4
        """
        started_at = time.perf_counter()

        # Node 1: split
        segments = await self.node1_query_splitter(user_text)
        print(f"[ORCH] node1_done segments={len(segments)}")

        # Process all segments — accumulate results
        results: List[Dict[str, Any]] = []

        for idx, seg in enumerate(segments, start=1):
            print(f"[ORCH] segment {idx}/{len(segments)}: {self._preview(seg, 80)}")

            # Node 2: intent + constraint stripping
            intent_info = await self.node2_intent_router(seg)
            intent = intent_info.get('intent')
            constraints = intent_info.get('constraints', {})
            clean_query = intent_info.get('clean_query', seg)
            is_complex = intent_info.get('is_complex', False)

            # Skip greeting / thanks
            _SKIP_INTENTS = frozenset({"greeting", "thanks", "unknown", None, ""})
            if intent in _SKIP_INTENTS:
                greeting = (
                    "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. "
                    "Mình có thể giúp gì cho bạn?"
                )
                self.metrics.increment("tools.skipped_greeting_intent")
                results.append({
                    'segment': seg,
                    'intent': intent_info,
                    'raw_result': None,
                    'node3_subtype': None,
                })
                continue

            needs_agent = intent_info.get("needs_agent", False)
            node3_subtype = self._resolve_node3_subtype(intent)

            raw_result: Any = {"message": "No tool mapped", "items": []}

            if needs_agent:
                # Agent path: tool → agent_filter (bắt buộc cho subject_registration)
                self.metrics.increment("agent.invoked")
                try:
                    agent_started = time.perf_counter()
                    # Tool call
                    tool_res = await asyncio.wait_for(
                        self.tools.call(intent, {
                            "q": clean_query,
                            "student_id": student_id,
                            "conversation_id": conversation_id,
                        }),
                        timeout=AGENT_REASONING_TIMEOUT,
                    )
                    raw_result = tool_res if tool_res is not None else []

                    # Agent filter: BẮT BUỘC cho subject_registration, optional cho others
                    if intent == "subject_registration_suggestion":
                        filtered = await self._agent_filter(raw_result, constraints, seg)
                        raw_result = filtered
                    elif is_complex and any(
                        constraints.get(k)
                        for k in ("exclude_subjects", "forbidden_time_slots",
                                  "forbidden_times", "days")
                        if constraints.get(k)
                    ):
                        filtered = await self._agent_filter(raw_result, constraints, seg)
                        raw_result = filtered

                    agent_ms = (time.perf_counter() - agent_started) * 1000
                    print(f"[HANDLE][AGENT] intent={intent} done in {agent_ms:.1f}ms")
                except asyncio.TimeoutError:
                    self.metrics.increment("agent.timeout")
                    print(f"[HANDLE][AGENT] TIMEOUT → fallback")
                    fallback_res = await self.tools.call(intent, {
                        "q": clean_query,
                        "student_id": student_id,
                        "conversation_id": conversation_id,
                    })
                    self.metrics.increment("agent.fallback_to_rule")
                    raw_result = {
                        "status": "error",
                        "error": "Mình đang xử lý hơi chậm, đã quay về chế độ tra cứu nhanh. "
                                  "Kết quả dưới đây có thể chưa đầy đủ.",
                        "_fallback_raw": fallback_res,
                        "_fallback_reason": "agent_timeout",
                    }
            else:
                # Rule-based path
                try:
                    tool_started = time.perf_counter()
                    raw_result = await self.tools.call(intent, {
                        "q": clean_query,
                        "student_id": student_id,
                        "conversation_id": conversation_id,
                    })
                    if raw_result is None:
                        raw_result = []
                    tool_ms = (time.perf_counter() - tool_started) * 1000
                    self.metrics.increment(f"tools.{intent}.success")
                    print(f"[NODE-3][{node3_subtype or '?'}] intent={intent} done in {tool_ms:.1f}ms")
                except Exception as e:
                    self.metrics.increment(f"tools.{intent or 'unknown'}.failure")
                    err_msg = f"TOOLS_LAYER_UNEXPECTED: {type(e).__name__}: {e}"
                    print(f"[NODE-3] error: {err_msg}")
                    raw_result = {"status": "error", "error": err_msg}

            # Accumulate segment result
            results.append({
                'segment': seg,
                'intent': intent_info,
                'raw_result': raw_result,
                'node3_subtype': node3_subtype,
                'clean_query': clean_query,
                'constraints': constraints,
            })

        # Node 4: Response Formatter — synthesis for multi-segment
        node4_result = await self.node4_response_formatter(
            results,
            "Generate response",
            original_query=user_text,
            intent_hints=[r.get("intent", {}).get("intent") for r in results if r.get("intent")],
            segment_results=results,  # pass all for synthesis
        )
        formatted = node4_result["text"]

        # Summary intent
        if len(results) > 1:
            summary_intent = "compound"
            is_compound = True
            confidence_label = "medium"
            confidence_score = 0.6
        elif results:
            first = results[0].get("intent") or {}
            if isinstance(first, dict):
                summary_intent = first.get("intent", "unknown")
                confidence_score = self._normalize_confidence(first.get("confidence", 0.0))
            else:
                summary_intent = str(first) if first else "unknown"
                confidence_score = 0.0
            is_compound = False
            confidence_label = self._confidence_label(confidence_score)
        else:
            summary_intent = "unknown"
            confidence_score = 0.0
            is_compound = False
            confidence_label = "low"

        parts = [
            {
                "intent": item.get("intent"),
                "node3_subtype": item.get("node3_subtype"),
                "text": item.get("segment"),
                "data": item.get("raw_result"),
            }
            for item in results
        ]

        total_ms = (time.perf_counter() - started_at) * 1000
        print(f"[ORCH] done intent={summary_intent} segments={len(results)} duration={total_ms:.1f}ms")

        return {
            "raw": results,
            "response": formatted,
            "text": formatted,
            "intent": summary_intent,
            "confidence": confidence_label,
            "confidence_score": confidence_score,
            "is_compound": is_compound,
            "parts": parts,
            "debug": {
                "llm_processing_time_ms": node4_result.get("processing_time_ms"),
                "model_used": node4_result.get("model_used"),
                "from_cache": node4_result.get("from_cache", False),
                "node3_subtypes": [r.get("node3_subtype") for r in results],
                "node3_outputs": [r.get("raw_result") for r in results],
                "synthesized": node4_result.get("synthesized", False),
            }
        }

    async def node1_query_splitter(self, text: str) -> List[str]:
        started_at = time.perf_counter()
        split_regex = re.compile(
            r"\s*(?:,|;)?\s*(?:sau đó|đồng thời|và|tiếp theo|rồi)\s+",
            re.IGNORECASE,
        )
        connector_regex = re.compile(
            r"(?:sau đó|đồng thời|và|tiếp theo|rồi)",
            re.IGNORECASE,
        )

        fallback_segments = [text]
        if connector_regex.search(text):
            parts = [part.strip(" ,;") for part in split_regex.split(text) if part.strip(" ,;")]
            uncertain = len(parts) < 2 or any(len(part.split()) < 2 for part in parts)
            uncertain = uncertain or any(
                part.lower().startswith(("không muốn", "tránh", "ngoại trừ", "không học", "thay vì"))
                for part in parts[1:]
            )
            fallback_segments = parts or [text]
            if len(parts) >= 2 and not uncertain:
                self.metrics.increment("node1.multi_intent_split")
                duration = time.perf_counter() - started_at
                self.metrics.observe_latency("node1.latency", duration)
                print(f"[NODE-1:SPLIT] regex -> {len(parts)} segments")
                return parts

        try:
            res = await self.llm.split(
                text,
                timeout=NODE1_TIMEOUT,
                max_tokens=NODE1_SPLIT_MAX_TOKENS,
                temperature=0.0,
            )
            segments = res.get("segments") or fallback_segments
            self.metrics.increment("node1.llm_success")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] LLM -> {len(segments)} segments")
            return segments
        except Exception as exc:
            self.metrics.increment("node1.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] fallback: {exc} -> {len(fallback_segments)} segments")
            return fallback_segments or [text]

    async def node4_response_formatter(
        self,
        raw_result: Any,
        instruction: str,
        original_query: Optional[str] = None,
        intent_hints: Optional[List[str]] = None,
        segment_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        seg_results = segment_results or []

        if len(seg_results) >= 2:
            return await self._synthesize_multi_segment(seg_results, original_query or instruction, started_at)

        intent = None
        if intent_hints:
            intent = next((item for item in intent_hints if item), None)
        if intent is None and isinstance(raw_result, dict):
            intent = raw_result.get("intent")
            if intent is None and isinstance(raw_result.get("data"), dict):
                intent = raw_result["data"].get("intent")

        text = format_rule_based_response(raw_result, intent, original_query or instruction)
        total_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.observe_latency("node4.latency", total_ms / 1000)
        self.metrics.increment("node4.rule_based_success")
        return {
            "text": text,
            "from_cache": False,
            "processing_time_ms": 0.0,
            "model_used": "rule_based",
        }

    async def _synthesize_multi_segment(
        self,
        segment_results: List[Dict[str, Any]],
        original_query: str,
        started_at: float,
    ) -> Dict[str, Any]:
        text = join_rule_based_segments([item.get("formatted_text", "") for item in segment_results])
        total_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.observe_latency("node4_synthesize.latency", total_ms / 1000)
        self.metrics.increment("node4_synthesize.rule_based_success")
        return {
            "text": text,
            "from_cache": False,
            "processing_time_ms": 0.0,
            "model_used": "rule_based_join",
            "synthesized": True,
        }

    async def _agent_filter(
        self,
        raw_data: Any,
        constraints: Dict[str, Any],
        seg: str,
    ) -> Any:
        excluded = [
            str(item).lower().strip()
            for item in constraints.get("exclude_subjects", [])
            if str(item).strip()
        ]
        if not excluded:
            return raw_data

        payload = raw_data
        if isinstance(raw_data, dict) and "status" in raw_data and "data" in raw_data:
            payload = raw_data.get("data")

        rows = None
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            rows = payload.get("data")

        if rows is None:
            return raw_data

        filtered_rows = [
            row
            for row in rows
            if not any(term in str(row.get("subject_name", "")).lower() for term in excluded)
        ]
        payload["data"] = filtered_rows
        if isinstance(raw_data, dict) and "status" in raw_data and "data" in raw_data:
            raw_data["data"] = payload
            return raw_data
        return payload

    async def _execute_segment_parallel(
        self,
        seg: str,
        intent_info: Dict[str, Any],
        student_id: Optional[int],
        conversation_id: Optional[int],
    ) -> Dict[str, Any]:
        intent = intent_info.get("intent")
        constraints = intent_info.get("constraints", {})
        clean_query = intent_info.get("clean_query", seg)
        node3_subtype = self._resolve_node3_subtype(intent)

        if intent in ("greeting", "thanks"):
            text = (
                "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?"
                if intent == "greeting"
                else "Rất vui được giúp đỡ bạn. Nếu cần thêm thông tin, bạn cứ hỏi tiếp."
            )
            return {
                "segment": seg,
                "intent": intent_info,
                "raw_result": {"text": text, "intent": intent},
                "node3_subtype": None,
                "clean_query": clean_query,
                "constraints": constraints,
            }

        if intent in ("unknown", None, ""):
            return {
                "segment": seg,
                "intent": intent_info,
                "raw_result": {"text": "Mình chưa hiểu rõ yêu cầu này, bạn vui lòng diễn đạt lại ngắn gọn hơn."},
                "node3_subtype": None,
                "clean_query": clean_query,
                "constraints": constraints,
            }

        try:
            raw_result = await asyncio.wait_for(
                self.tools.call(
                    intent,
                    {
                        "q": clean_query,
                        "student_id": student_id,
                        "conversation_id": conversation_id,
                    },
                ),
                timeout=TOOL_EXECUTION_TIMEOUT,
            )
            if intent == "subject_registration_suggestion" or constraints.get("exclude_subjects"):
                raw_result = await self._agent_filter(raw_result, constraints, seg)
        except Exception as exc:
            raw_result = {"status": "error", "error": str(exc)}

        formatted_text = format_rule_based_response(raw_result, intent, seg)
        return {
            "segment": seg,
            "intent": intent_info,
            "raw_result": raw_result,
            "formatted_text": formatted_text,
            "node3_subtype": node3_subtype,
            "clean_query": clean_query,
            "constraints": constraints,
        }

    async def _run_parallel_pipeline(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        pre_split_segments: Optional[List[str]] = None,
        fallback_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        segments = pre_split_segments or await self.node1_query_splitter(user_text)
        print(f"[ORCH] node1_done segments={len(segments)}")

        try:
            intent_infos = await asyncio.wait_for(
                asyncio.gather(*(self.node2_intent_router(seg) for seg in segments)),
                timeout=LLM_REASONING_TIMEOUT,
            )
        except Exception as exc:
            text = "Mình chưa phân tích kịp yêu cầu trong thời gian cho phép. Bạn vui lòng thử lại hoặc chia nhỏ câu hỏi giúp mình."
            print(f"[ORCH] reasoning_fallback error={exc}")
            return {
                "raw": [],
                "response": text,
                "text": text,
                "intent": "unknown",
                "confidence": "low",
                "confidence_score": 0.0,
                "is_compound": False,
                "parts": [],
                "debug": {
                    "fallback_mode": fallback_mode or "reasoning_fallback",
                    "model_used": "rule_based_fallback",
                    "from_cache": False,
                },
            }

        segment_results: List[Optional[Dict[str, Any]]] = [None] * len(segments)

        async def _run_and_store(index: int, seg: str, intent_info: Dict[str, Any]) -> Dict[str, Any]:
            result = await self._execute_segment_parallel(seg, intent_info, student_id, conversation_id)
            segment_results[index] = result
            return result

        tasks = [
            _run_and_store(index, seg, intent_info)
            for index, (seg, intent_info) in enumerate(zip(segments, intent_infos))
        ]
        await asyncio.gather(*tasks)
        results = [item for item in segment_results if item is not None]

        node4_result = await self.node4_response_formatter(
            results,
            "Generate response",
            original_query=user_text,
            intent_hints=[r.get("intent", {}).get("intent") for r in results if r.get("intent")],
            segment_results=results,
        )
        formatted = node4_result["text"]

        if len(results) > 1:
            summary_intent = "compound"
            confidence_label = "medium"
            confidence_score = 0.6
            is_compound = True
        elif results:
            first = results[0].get("intent") or {}
            summary_intent = first.get("intent", "unknown") if isinstance(first, dict) else "unknown"
            confidence_score = self._normalize_confidence(first.get("confidence", 0.0)) if isinstance(first, dict) else 0.0
            confidence_label = self._confidence_label(confidence_score)
            is_compound = False
        else:
            summary_intent = "unknown"
            confidence_label = "low"
            confidence_score = 0.0
            is_compound = False

        total_ms = (time.perf_counter() - started_at) * 1000
        print(f"[ORCH] parallel_done intent={summary_intent} segments={len(results)} duration={total_ms:.1f}ms")
        return {
            "raw": results,
            "response": formatted,
            "text": formatted,
            "intent": summary_intent,
            "confidence": confidence_label,
            "confidence_score": confidence_score,
            "is_compound": is_compound,
            "parts": [
                {
                    "intent": item.get("intent"),
                    "node3_subtype": item.get("node3_subtype"),
                    "text": item.get("segment"),
                    "data": item.get("raw_result"),
                }
                for item in results
            ],
            "debug": {
                "fallback_mode": fallback_mode,
                "llm_processing_time_ms": node4_result.get("processing_time_ms"),
                "model_used": node4_result.get("model_used"),
                "from_cache": node4_result.get("from_cache", False),
                "node3_subtypes": [r.get("node3_subtype") for r in results],
            },
        }

    async def _handle_graph(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        pre_segments = await self.node1_query_splitter(user_text)
        if len(pre_segments) > 1:
            return await self._run_parallel_pipeline(
                user_text,
                student_id,
                conversation_id,
                pre_split_segments=pre_segments,
            )

        from app.agents.agent_graph import run_graph_for_orchestrator
        try:
            return await asyncio.wait_for(
                run_graph_for_orchestrator(user_text, student_id, conversation_id),
                timeout=AGENT_REASONING_TIMEOUT,
            )
        except Exception as exc:
            print(f"[ORCH:GRAPH] fallback_to_parallel error={exc}")
            self.metrics.increment("agent.graph_error_fallback")
            return await self._run_parallel_pipeline(
                user_text,
                student_id,
                conversation_id,
                fallback_mode="direct_node3",
            )

    async def _handle_direct_node3_fallback(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self._run_parallel_pipeline(
            user_text,
            student_id,
            conversation_id,
            fallback_mode="direct_node3",
        )

    async def _handle_linear(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self._run_parallel_pipeline(user_text, student_id, conversation_id)

    async def node2_intent_router(self, text: str) -> Dict[str, Any]:
        started_at = time.perf_counter()
        constraint_regex = re.compile(
            r"(?:tôi\s+)?(?:không\s+muốn|tránh|ngoại\s+trừ|không\s+học|thay\s+vì)[^,;\.]*",
            re.IGNORECASE,
        )

        constraint_phrases = [match.group(0).strip() for match in constraint_regex.finditer(text)]
        clean_query = text
        for phrase in constraint_phrases:
            clean_query = clean_query.replace(phrase, "")
        clean_query = re.sub(r"[,;\s]{2,}", " ", clean_query).strip(" ,;") or text

        exclude_subjects: List[str] = []
        for phrase in constraint_phrases:
            normalized = re.sub(
                r"^(?:tôi\s+)?(?:không\s+muốn|tránh|ngoại\s+trừ|không\s+học|thay\s+vì)\s*",
                "",
                phrase,
                flags=re.IGNORECASE,
            ).strip(" ,.;")
            for part in re.split(r",|;|\s+và\s+|\s+hoặc\s+", normalized):
                cleaned = re.sub(r"^(?:môn|học phần|lớp)\s+", "", part, flags=re.IGNORECASE).strip()
                if cleaned:
                    exclude_subjects.append(cleaned)

        constraints: Dict[str, Any] = {
            "constraint_phrases": constraint_phrases,
            "exclude_subjects": exclude_subjects,
            "forbidden_time_slots": [],
            "forbidden_times": [],
            "semester": None,
            "days": [],
        }

        is_complex = bool(constraint_phrases) or self._is_complex_query(text)
        lowered = _normalize_text(clean_query)
        if constraint_phrases and any(keyword in lowered for keyword in ("dang ky", "nen hoc", "tu van mon")):
            return {
                "intent": "subject_registration_suggestion",
                "confidence": 0.95,
                "source": "keyword_bias",
                "needs_agent": True,
                "is_complex": True,
                "constraints": constraints,
                "clean_query": clean_query,
            }
        if constraint_phrases and any(keyword in lowered for keyword in ("đăng ký", "đăng kí", "nên học", "tư vấn môn")):
            return {
                "intent": "subject_registration_suggestion",
                "confidence": 0.95,
                "source": "keyword_bias",
                "needs_agent": True,
                "is_complex": True,
                "constraints": constraints,
                "clean_query": clean_query,
            }

        if self.tfidf and clean_query:
            try:
                tfidf_res = await self.tfidf.classify_intent(clean_query)
                label = tfidf_res.get("intent", "unknown")
                score = tfidf_res.get("confidence_score", 0.0)
                if score >= INTENT_CONF_THRESHOLD:
                    duration = time.perf_counter() - started_at
                    self.metrics.increment("node2.tfidf_hit")
                    self.metrics.observe_latency("node2.latency", duration)
                    return {
                        "intent": label,
                        "confidence": score,
                        "source": "tfidf",
                        "needs_agent": is_complex,
                        "is_complex": is_complex,
                        "constraints": constraints,
                        "clean_query": clean_query,
                    }
            except Exception as exc:
                print(f"[NODE-2] TF-IDF failed: {exc}")

        try:
            llm_res = await self.llm.classify(
                clean_query,
                timeout=NODE2_TIMEOUT,
                max_tokens=NODE2_CLASSIFY_MAX_TOKENS,
                temperature=0.0,
            )
            intent = llm_res.get("intent") or "unknown"
            confidence = self._normalize_confidence(llm_res.get("confidence", 0.0))
            duration = time.perf_counter() - started_at
            self.metrics.increment("node2.llm_success")
            self.metrics.observe_latency("node2.latency", duration)
            return {
                "intent": intent,
                "confidence": confidence,
                "source": "llm",
                "needs_agent": True,
                "is_complex": is_complex,
                "constraints": constraints,
                "clean_query": clean_query,
            }
        except Exception as exc:
            duration = time.perf_counter() - started_at
            self.metrics.increment("node2.fallback")
            self.metrics.observe_latency("node2.latency", duration)
            print(f"[NODE-2] fallback: {exc}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": "fallback",
                "needs_agent": False,
                "is_complex": is_complex,
                "constraints": constraints,
                "clean_query": clean_query,
            }
