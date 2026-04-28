import hashlib
import json
import os
import time
import traceback
from typing import Any, Dict, List, Optional

from app.llm.llm_client import LLMClient
from app.llm.llm_client import LLMCircuitOpenError
from app.llm.response_cache import ResponseCache
from .orchestration_metrics import get_orchestration_metrics
from .tools_registry import ToolsRegistry

INTENT_CONF_THRESHOLD = float(os.environ.get("INTENT_CONF_THRESHOLD", "0.6"))
NODE1_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "48"))
NODE2_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "12"))
NODE4_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "150"))
NODE4_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.1"))
NODE4_GENERATE_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
NODE4_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
NODE1_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", os.environ.get("LLM_CLASSIFY_TIMEOUT", "30.0")))
NODE2_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "20.0"))
NODE4_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "10.0"))

try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None

# Fields to REMOVE from data before sending to Node 4 (not needed for formatting)
_TRIM_FIELDS = frozenset({
    "_student_course_pk", "_in_student_program", "_student_learning_status",
    "_student_grade_history", "_student_latest_grade", "_student_latest_semester",
    "_student_course_name", "_student_context_message", "_intent_type",
    "_id", "_score", "_rank",
})

# Max items per list to prevent token explosion
_MAX_ITEMS_PER_LIST = 20


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
        """
        Remove unnecessary fields from data to reduce tokens.
        """
        if isinstance(data, dict):
            return {
                k: self._trim_data(v)
                for k, v in data.items()
                if k not in _TRIM_FIELDS
            }
        elif isinstance(data, list):
            if len(data) > _MAX_ITEMS_PER_LIST:
                return self._trim_data(data[:_MAX_ITEMS_PER_LIST])
            return [self._trim_data(item) for item in data]
        return data

    def _is_data_empty(self, data: Any) -> bool:
        """
        Check if the data from Node 3 is empty or indicates an error.
        Handles FastAPI envelope: {"status": "error", "error": "...", ...}

        Special case: text-only responses (e.g. preference-collection questions
        from class_registration_suggestion) have a meaningful "text" field but
        no "data" key — these are NOT empty.
        """
        if data is None:
            return True
        if isinstance(data, list) and len(data) == 0:
            return True
        if isinstance(data, dict):
            # FastAPI error envelope
            if data.get("status") == "error" or data.get("error"):
                return True
            if data.get("sql_error"):
                return True
            # Check for empty data structures
            keys_that_matter = ["data", "result", "text", "rows", "items"]
            for key in keys_that_matter:
                if key in data:
                    val = data[key]
                    if val is None:
                        continue
                    if isinstance(val, list) and len(val) == 0:
                        continue
                    # Non-empty value found — NOT empty
                    return False
            # Text-only response (no "data" key, but has non-empty "text"):
            # NOT empty — Node-4 should pass this to the LLM to format.
            text_val = data.get("text")
            if isinstance(text_val, str) and text_val.strip():
                return False
            # If only metadata/info keys present, check if actual data is missing
            if not any(k in data for k in keys_that_matter):
                return True
        if isinstance(data, str) and data.strip() == "":
            return True
        return False

    def _extract_result_data(self, raw_result: Any) -> Any:
        """
        Extract the actual result data from various raw_result formats:
        1. FastAPI envelope:  {"status": "...", "data": {"text":..., "data":[...]}}
        2. Segment wrapper:    {"segment": "...", "raw_result": {...}}
        3. Preference wrapper: {"text": ..., "is_preference_collecting": true, ...}
        4. Plain dict/list
        """
        if raw_result is None:
            return None

        # Unwrap FastAPI envelope first
        if isinstance(raw_result, dict):
            if "status" in raw_result and "data" in raw_result:
                inner = raw_result["data"]
                # Recursively unwrap inner data
                return self._extract_result_data(inner)

            # Unwrap segment wrapper
            if "segment" in raw_result or "raw_result" in raw_result:
                inner = raw_result.get("raw_result", raw_result)
                return self._extract_result_data(inner)

            # Preserve text-based responses (preference-collection questions,
            # instructions, etc.) as-is — they have text but no "data" key.
            text_val = raw_result.get("text")
            if isinstance(text_val, str) and text_val.strip():
                # Keep the whole dict so Node-4 sees intent + text + metadata
                return raw_result

            return raw_result

        if isinstance(raw_result, list):
            if len(raw_result) == 0:
                return None
            # Single-item list
            if len(raw_result) == 1:
                return self._extract_result_data(raw_result[0])
            # Multi-item list — extract data from each
            extracted = []
            for item in raw_result:
                extracted.append(self._extract_result_data(item))
            return extracted

        return raw_result

    def _compact_data_for_prompt(self, raw_result: Any, intent_hints: Optional[List[str]] = None) -> str:
        """
        Convert data to compact string format for minimal token usage.
        intent_hints: list of intent names; if "class_registration_suggestion" is present,
        the "text" field (preference question) is preserved as top priority.
        """
        trimmed = self._trim_data(raw_result)

        # Special handling for preference-collection responses (class_registration_suggestion)
        is_preference_intent = (
            intent_hints is not None
            and any(
                i in ("class_registration_suggestion", "subject_registration_suggestion")
                for i in intent_hints
            )
        )

        if isinstance(trimmed, dict):
            # If this is a preference question response, surface the text prominently
            if is_preference_intent and "text" in trimmed:
                text_val = trimmed.get("text", "")
                if isinstance(text_val, str) and text_val.strip():
                    return f"[Câu hỏi từ hệ thống]\n{text_val}"
            # Fall through to normal list handling below

        if isinstance(trimmed, list):
            lines = []
            for i, item in enumerate(trimmed):
                if isinstance(item, dict):
                    seg = item.get('segment', f'Phần {i+1}')
                    res = item.get('raw_result', item)

                    # Special: for preference-intent results, show text first
                    if is_preference_intent and isinstance(res, dict) and "text" in res:
                        text_val = res.get("text", "")
                        if isinstance(text_val, str) and text_val.strip():
                            lines.append(f"[{seg}] [Câu hỏi] {text_val}")
                            continue

                    if isinstance(res, dict):
                        # Extract only essential fields
                        essential = {}
                        for k, v in res.items():
                            if isinstance(v, (str, int, float, bool)) or v is None:
                                essential[k] = v
                            elif isinstance(v, list) and len(v) <= 5:
                                essential[k] = v

                        # Compact format: key1=val1, key2=val2...
                        parts = [f"{k}={v}" for k, v in essential.items() if v is not None][:10]
                        res_str = ", ".join(parts)
                    else:
                        res_str = str(res)[:100]

                    lines.append(f"[{seg}] {res_str}")
                else:
                    lines.append(str(item)[:100])

            return "\n".join(lines)[:2000]  # Cap at 2000 chars
        else:
            return str(trimmed)[:1000]

    def _build_formatter_prompt(
        self,
        raw_result: Any,
        instruction: str,
        original_query: Optional[str] = None,
        intent_hints: Optional[List[str]] = None,
    ) -> str:
        """
        Build prompt for Node 4 with the format:
          Dữ liệu hệ thống trả về: {JSON_RESULT}
          Câu hỏi người dùng: {ORIGINAL_QUERY}
          Intent: {INTENT_HINTS}  (optional — for preference-collection context)
        """
        # Extract the actual result data
        extracted = self._extract_result_data(raw_result)
        compact = self._compact_data_for_prompt(extracted, intent_hints=intent_hints)

        # Wrap in JSON format
        import json
        try:
            json_data = json.dumps(extracted, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            json_data = str(extracted) if extracted is not None else "{}"

        # Build the prompt
        prompt_parts = []
        prompt_parts.append(f"Dữ liệu hệ thống trả về: {json_data}")

        if original_query:
            prompt_parts.append(f"Câu hỏi người dùng: {original_query}")
        else:
            prompt_parts.append(f"Câu hỏi người dùng: {instruction}")

        # Include intent context so LLM knows this is a preference question vs SQL result
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
        if c < 0.0:
            return 0.0
        if c > 1.0:
            return 1.0
        return c

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.5:
            return "medium"
        return "low"

    def _derive_summary_intent(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {"intent": "unknown", "confidence": 0.0, "confidence_label": "low", "is_compound": False}
        if len(results) > 1:
            return {"intent": "compound", "confidence": 0.6, "confidence_label": "medium", "is_compound": True}
        intent_info = results[0].get("intent") or {}
        intent = intent_info.get("intent") if isinstance(intent_info, dict) else "unknown"
        confidence = self._normalize_confidence(intent_info.get("confidence") if isinstance(intent_info, dict) else 0.0)
        return {
            "intent": intent or "unknown",
            "confidence": confidence,
            "confidence_label": self._confidence_label(confidence),
            "is_compound": False,
        }

    # ── Node 3 subtype constants ─────────────────────────────────────────────────
    # Maps top-level intent → which Node-3 processor handled it.
    _NODE3A_INTENTS = frozenset({
        "subject_info", "class_info", "grade_view",
        "learned_subjects_view", "schedule_view", "schedule_info", "student_info",
    })
    _NODE3B_INTENTS = frozenset({"subject_registration_suggestion"})
    _NODE3C_INTENTS = frozenset({"class_registration_suggestion"})
    _NODE3D_INTENTS = frozenset({"modify_schedule"})

    def _resolve_node3_subtype(self, intent: Optional[str]) -> Optional[str]:
        """Return the Node-3 sub-type label (e.g. 'node3a') for a given intent."""
        if intent in self._NODE3A_INTENTS:
            return "node3a"   # NL2SQL
        if intent in self._NODE3B_INTENTS:
            return "node3b"   # Gợi ý học tập (subject)
        if intent in self._NODE3C_INTENTS:
            return "node3c"   # Gợi ý đăng ký (class)
        if intent in self._NODE3D_INTENTS:
            return "node3d"   # Điều chỉnh thời khóa biểu
        return None

    def _preview(self, value: Any, max_len: int = 140) -> str:
        text = self._stable_payload(value)
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    async def node1_query_splitter(self, text: str) -> List[str]:
        started_at = time.perf_counter()
        print(f"[NODE-1:SPLIT] input={self._preview(text, 120)}")
        
        if len(text.split()) < 40 and ('?' not in text and ',' not in text and '.' not in text):
            self.metrics.increment("node1.heuristic_hit")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] source=heuristic segments=1 duration_ms={duration * 1000:.1f}")
            return [text]
        
        try:
            res = await self.llm.split(
                text,
                timeout=NODE1_TIMEOUT,
                max_tokens=NODE1_SPLIT_MAX_TOKENS,
                temperature=0.0,
            )
            segments = res.get('segments') or [text]
            self.metrics.increment("node1.llm_success")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(
                f"[NODE-1:SPLIT] source=llm segments={len(segments)} "
                f"duration_ms={duration * 1000:.1f}"
            )
            return segments
        except Exception as exc:
            self.metrics.increment("node1.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            fallback_segments = [s.strip() for s in text.replace('?', '.').split('.') if s.strip()]
            print(f"[NODE-1:SPLIT] source=fallback error={exc} segments={len(fallback_segments)}")
            return fallback_segments

    async def node2_intent_router(self, text: str) -> Dict[str, Any]:
        started_at = time.perf_counter()
        print(f"[NODE-2:ROUTE] query={self._preview(text, 120)}")
        
        label = 'unknown'
        score = 0.0
        if self.tfidf:
            tfidf_res = await self.tfidf.classify_intent(text)
            label = tfidf_res.get("intent", "unknown")
            score = tfidf_res.get("confidence_score", 0.0)
            if score >= INTENT_CONF_THRESHOLD or len(text.split()) <= 20:
                self.metrics.increment("node2.tfidf_hit")
                duration = time.perf_counter() - started_at
                self.metrics.observe_latency("node2.latency", duration)
                print(f"[NODE-2:ROUTE] source=tfidf intent={label} confidence={score:.3f} duration_ms={duration * 1000:.1f}")
                return {"intent": label, "confidence": score, "source": "tfidf"}
        
        try:
            llm_res = await self.llm.classify(
                text,
                timeout=NODE2_TIMEOUT,
                max_tokens=NODE2_CLASSIFY_MAX_TOKENS,
                temperature=0.0,
            )
            intent = llm_res.get('intent') or llm_res.get('label')
            confidence = self._normalize_confidence(llm_res.get('confidence', 0.0))
            self.metrics.increment("node2.llm_success")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node2.latency", duration)
            print(f"[NODE-2:ROUTE] source=llm intent={intent} confidence={confidence:.3f} duration_ms={duration * 1000:.1f}")
            return {"intent": intent, "confidence": confidence, "source": "llm"}
        except Exception as exc:
            self.metrics.increment("node2.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node2.latency", duration)
            fallback_intent = label if self.tfidf else 'unknown'
            fallback_score = score if self.tfidf else 0.0
            print(f"[NODE-2:ROUTE] source=fallback intent={fallback_intent} error={exc}")
            return {"intent": fallback_intent, "confidence": fallback_score, "source": "fallback"}

    async def node4_response_formatter(
        self,
        raw_result: Any,
        instruction: str,
        original_query: Optional[str] = None,
        intent_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Node 4: Format raw data into friendly response.
        - Anti-hallucination: if data is empty/error, return fallback message instead of calling LLM.
        - Prompt format: "Dữ liệu hệ thống trả về: {JSON}  Câu hỏi người dùng: {ORIGINAL_QUERY}"
        - intent_hints: list of intent names (e.g. ["class_registration_suggestion"]) so Node-4
          knows whether this is a preference-collection question vs a SQL result.
        Returns dict with 'text' and debug info.
        """
        started_at = time.perf_counter()
        llm_processing_time_ms = 0.0
        model_used = "none"

        # ── LOG INPUT DATA ──────────────────────────────────────────────────────
        try:
            print(f"\n{'='*60}")
            print(f"[NODE-4:INPUT] Raw data from Node-3:")
            if isinstance(raw_result, list):
                for i, item in enumerate(raw_result):
                    print(f"  [{i+1}] segment: {item.get('segment', 'N/A')}")
                    raw = item.get('raw_result', {})
                    if isinstance(raw, dict):
                        for k, v in list(raw.items())[:5]:
                            print(f"      {k}: {v}")
                    elif isinstance(raw, list):
                        print(f"      (list with {len(raw)} items)")
            else:
                print(f"  Type: {type(raw_result).__name__}")
                print(f"  Content: {str(raw_result)[:500]}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"[NODE-4:INPUT] Error logging input: {e}")

        # ── STEP 1: Extract data FIRST (before cache check) ─────────────────────
        # This ensures the cache key is stable regardless of envelope wrapping.
        extracted_data = self._extract_result_data(raw_result)

        # ── STEP 2: Anti-hallucination guard on extracted data ──────────────────
        if self._is_data_empty(extracted_data):
            print("[NODE-4:ANTI-HALLU] Data is empty or error — returning fallback message.")
            self.metrics.increment("node4.empty_data")
            total_duration_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4.latency", total_duration_ms / 1000)
            fallback_text = (
                "Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. "
                "Bạn vui lòng kiểm tra lại nhé!"
            )
            return {
                "text": fallback_text,
                "from_cache": False,
                "processing_time_ms": 0.0,
                "model_used": "none",
                "empty_data_guard": True,
            }

        # ── STEP 3: Extract original query from results ─────────────────────────
        if original_query is None:
            if isinstance(raw_result, list) and len(raw_result) > 0:
                original_query = raw_result[0].get("segment", instruction)
            elif isinstance(raw_result, dict):
                original_query = raw_result.get("segment", instruction)
            else:
                original_query = instruction

        # ── STEP 4: Cache check — use extracted data for stable key ─────────────
        cache_key_data = extracted_data  # stable key from clean extracted data
        h = self._hash_raw_result(cache_key_data, instruction)
        cached = self.cache.get(h)
        if cached:
            self.metrics.increment("node4.cache_hit")
            cache_duration_ms = (time.perf_counter() - started_at) * 1000
            self.metrics.observe_latency("node4.latency", cache_duration_ms / 1000)
            return {"text": cached, "from_cache": True, "processing_time_ms": 0, "model_used": "cache"}

        self.metrics.increment("node4.cache_miss")

        # ── STEP 5: Build prompt with few-shot examples using extracted data ─────
        prompt = self._build_formatter_prompt(extracted_data, instruction, original_query, intent_hints=intent_hints)

        # ── Few-shot examples for professional academic assistant style ──────────
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

Ví dụ 4:
- Dữ liệu: {"subject_name": "Ngữ văn 1", "credits": 3, "teacher_name": "Nguyễn Văn A"}
- Câu hỏi: Thông tin môn Ngữ văn 1?
- Trả lời: Môn Ngữ văn 1 có 3 tín chỉ, giảng viên Nguyễn Văn A.
"""
        prompt = prompt + "\n" + _FEW_SHOT

        try:
            # Call LLM with 10s timeout to prevent system hanging
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
            model_used = gen.get('model_used', 'gemini')

            if not text:
                raise ValueError("LLM returned empty text")

            self.metrics.increment("node4.llm_success")

        except LLMCircuitOpenError:
            self.metrics.increment("node4.circuit_open")
            text = (
                "Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. "
                "Bạn vui lòng kiểm tra lại nhé!"
            )
            model_used = "circuit_open"

        except Exception as exc:
            self.metrics.increment("node4.fallback")
            error_detail = traceback.format_exc()
            print(f"[NODE-4:ERROR] {type(exc).__name__}: {str(exc)}")
            print(f"[NODE-4:ERROR] Stack:\n{error_detail}")
            text = (
                "Rất tiếc, mình không tìm thấy thông tin này trong hệ thống. "
                "Bạn vui lòng kiểm tra lại nhé!"
            )
            model_used = "error"
            llm_processing_time_ms = 0

        # Cache result
        self.cache.set(h, text)

        total_duration_ms = (time.perf_counter() - started_at) * 1000
        self.metrics.observe_latency("node4.latency", total_duration_ms / 1000)
        print(f"[NODE-4:DONE] duration={total_duration_ms:.1f}ms (LLM: {llm_processing_time_ms:.1f}ms) model={model_used}")

        return {
            "text": text,
            "from_cache": False,
            "processing_time_ms": llm_processing_time_ms,
            "model_used": model_used,
        }

    async def handle(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        handle_started_at = time.perf_counter()
        print(f"[ORCH] start query={self._preview(user_text, 120)} student_id={student_id}")
        
        # node 1 split
        segments = await self.node1_query_splitter(user_text)
        print(f"[ORCH] node1_done segments={len(segments)}")
        
        results = []
        for idx, seg in enumerate(segments, start=1):
            print(f"[ORCH] segment {idx}/{len(segments)}: {self._preview(seg, 80)}")

            # node 2 intent
            intent_info = await self.node2_intent_router(seg)
            intent = intent_info.get('intent')

            # ── GUARD: Skip greeting / thanks / unknown intents immediately ───────
            # These should return a static greeting without any LLM / Node-3 processing.
            _SKIP_INTENTS = frozenset({"greeting", "thanks", "unknown", None, ""})
            if intent in _SKIP_INTENTS:
                greeting = (
                    "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. "
                    "Mình có thể giúp gì cho bạn?"
                )
                self.metrics.increment("tools.skipped_greeting_intent")
                print(f"[ORCH] intent={intent!r} — returning greeting, skipping Node-3 and Node-4")
                return {
                    "raw": [],
                    "response": greeting,
                    "text": greeting,
                    "intent": "greeting",
                    "confidence": "high",
                    "confidence_score": 1.0,
                    "is_compound": False,
                    "parts": [],
                    "debug": {
                        "llm_processing_time_ms": None,
                        "model_used": "none",
                        "from_cache": False,
                        "skipped_reason": "greeting_intent",
                    },
                }

            node3_subtype = self._resolve_node3_subtype(intent)

            if not intent or intent == 'unknown':
                self.metrics.increment("tools.skipped_unknown_intent")
                res = {'message': 'No tool mapped', 'items': []}
            else:
                try:
                    tool_started = time.perf_counter()
                    res = await self.tools.call(
                        intent,
                        {
                            "q": seg,
                            "student_id": student_id,
                            "conversation_id": conversation_id,
                        },
                    )
                    if res is None:
                        res = []
                    tool_duration = (time.perf_counter() - tool_started) * 1000
                    self.metrics.increment(f"tools.{intent}.success")
                    print(
                        f"[NODE-3][{node3_subtype or '?'}] intent={intent} done in {tool_duration:.1f}ms"
                    )
                except Exception as e:
                    self.metrics.increment(f"tools.{intent or 'unknown'}.failure")
                    res = {"error": str(e)}
                    print(f"[NODE-3] ERROR [{node3_subtype or '?'}] intent={intent}: {e}")

            results.append({
                'segment': seg,
                'intent': intent_info,
                'raw_result': res,
                'node3_subtype': node3_subtype,
            })

        # node 4 response formatter
        node4_result = await self.node4_response_formatter(
            results,
            "Generate response",
            original_query=user_text,
            intent_hints=[r.get("intent", {}).get("intent") for r in results],
        )
        formatted = node4_result["text"]

        # Build debug info for llm_processing
        llm_processing = {
            "user_input": user_text,
            "llm_processed_output": formatted[:500] if formatted else None,
            "raw_data": {
                "segments": len(results),
                "intents": [r.get("intent", {}).get("intent") for r in results if r.get("intent")],
                "node3_subtypes": [r.get("node3_subtype") for r in results],
                "node3_outputs": [
                    r.get("raw_result") for r in results
                ],
            },
            "has_repetition": False,
            "processing_time_ms": node4_result.get("processing_time_ms"),
            "model_used": node4_result.get("model_used"),
            "from_cache": node4_result.get("from_cache", False),
        }

        summary = self._derive_summary_intent(results)
        parts = [
            {
                "intent": item.get("intent"),
                "node3_subtype": item.get("node3_subtype"),
                "text": item.get("segment"),
                "data": item.get("raw_result"),
            }
            for item in results
        ]

        total_duration = (time.perf_counter() - handle_started_at) * 1000
        print(f"[ORCH] done intent={summary['intent']} duration={total_duration:.1f}ms")

        return {
            "raw": results,
            "response": formatted,
            "text": formatted,
            "intent": summary["intent"],
            "confidence": summary["confidence_label"],
            "confidence_score": summary["confidence"],
            "is_compound": summary["is_compound"],
            "parts": parts,
            "debug": {
                "llm_processing_time_ms": node4_result.get("processing_time_ms"),
                "model_used": node4_result.get("model_used"),
                "from_cache": node4_result.get("from_cache", False),
                "node3_subtypes": [r.get("node3_subtype") for r in results],
                "node3_outputs": [r.get("raw_result") for r in results],
            }
        }
