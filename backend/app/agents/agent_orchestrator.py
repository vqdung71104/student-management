import hashlib
import json
import os
import time
import traceback
import time
from typing import Any, Dict, List, Optional

from click import prompt

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
NODE4_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "120.0"))

# placeholder import for local TF-IDF classifier
try:
    from app.chatbot.tfidf_classifier import TfidfIntentClassifier
except ImportError:
    TfidfIntentClassifier = None

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

    def _build_formatter_prompt(self, raw_result: Any, instruction: str) -> str:
        # Tối ưu: Nén dữ liệu thô thành văn bản đơn giản thay vì JSON rườm rà
        compact_data = ""
        if isinstance(raw_result, list):
            items = []
            for item in raw_result:
                seg = item.get('segment', '')
                res = item.get('raw_result', {})
                # Chỉ lấy phần nội dung chính, bỏ qua các metadata thừa
                if isinstance(res, dict):
                    content = res.get('items') or res.get('data') or res
                else:
                    content = res
                items.append(f"- Câu hỏi: {seg}\n  Dữ liệu: {content}")
            compact_data = "\n".join(items)
        else:
            compact_data = str(raw_result)

        # Prompt ngắn gọn, cố định phần đầu để tận dụng Prompt Caching
        return (
            "### Hướng dẫn: Bạn là trợ lý SV Bách Khoa. Tóm tắt dữ liệu sau bằng tiếng Việt ngắn gọn (1-3 câu). "
            "Tuyệt đối không bịa số liệu. Không chào hỏi.\n"
            f"### Dữ liệu:\n{compact_data}\n"
            "### Trả lời:"
        )

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

    def _preview(self, value: Any, max_len: int = 140) -> str:
        text = self._stable_payload(value)
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    async def node1_query_splitter(self, text: str) -> List[str]:
        started_at = time.perf_counter()
        print(f"[NODE-1:SPLIT] input={self._preview(text, 120)}")
        # quick local heuristics: 80% simple cases
        if len(text.split()) < 40 and ('?' not in text and ',' not in text and '.' not in text):
            self.metrics.increment("node1.heuristic_hit")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            print(f"[NODE-1:SPLIT] source=heuristic segments=1 duration_ms={duration * 1000:.1f}")
            return [text]
        # else ask LLM for complex queries
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
                f"duration_ms={duration * 1000:.1f} segments_preview={self._preview(segments, 160)}"
            )
            return segments
        except Exception as exc:
            # fallback to simple punctuation split
            self.metrics.increment("node1.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node1.latency", duration)
            fallback_segments = [s.strip() for s in text.replace('?', '.').split('.') if s.strip()]
            print(
                f"[NODE-1:SPLIT] source=fallback error={exc} segments={len(fallback_segments)} "
                f"duration_ms={duration * 1000:.1f}"
            )
            return fallback_segments

    async def node2_intent_router(self, text: str) -> Dict[str, Any]:
        started_at = time.perf_counter()
        print(f"[NODE-2:ROUTE] query={self._preview(text, 120)}")
        # Node-2: 
        # Giữ TFIDF làm chính
        # Chỉ gọi LLM khi confidence < 0.6 và query dài > 20 từ
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
                print(
                    f"[NODE-2:ROUTE] source=tfidf intent={label} confidence={score:.3f} "
                    f"duration_ms={duration * 1000:.1f}"
                )
                return {"intent": label, "confidence": score, "source": "tfidf"}
        # else fallback to LLM
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
            print(
                f"[NODE-2:ROUTE] source=llm intent={intent} confidence={confidence:.3f} "
                f"duration_ms={duration * 1000:.1f}"
            )
            return {"intent": intent, "confidence": confidence, "source": "llm"}
        except Exception as exc:
            self.metrics.increment("node2.fallback")
            duration = time.perf_counter() - started_at
            self.metrics.observe_latency("node2.latency", duration)
            fallback_intent = label if self.tfidf else 'unknown'
            fallback_score = score if self.tfidf else 0.0
            print(
                f"[NODE-2:ROUTE] source=fallback intent={fallback_intent} confidence={fallback_score:.3f} "
                f"error={exc} duration_ms={duration * 1000:.1f}"
            )
            return {"intent": fallback_intent, "confidence": fallback_score, "source": "fallback"}

    async def node4_response_formatter(self, raw_result: Any, instruction: str) -> str:
        started_at = time.perf_counter()

        # 1. IN RA DỮ LIỆU NHẬN ĐƯỢC TỪ NODE 3 (QUAN TRỌNG NHẤT)
        # Chúng ta dùng try-except nhỏ để in dữ liệu, tránh việc chính lệnh print gây lỗi
        try:
            data_type = type(raw_result).__name__
            # Nếu là list/dict thì format JSON cho dễ nhìn, nếu là object khác thì dùng str()
            if isinstance(raw_result, (list, dict)):
                data_preview = json.dumps(raw_result, indent=2, ensure_ascii=False)
            else:
                data_preview = str(raw_result)

            print("\n" + "="*50)
            print(f"[NODE-4:DEBUG] DỮ LIỆU NHẬN TỪ NODE-3:")
            print(f" - Kiểu dữ liệu: {data_type}")
            print(f" - Nội dung: {data_preview}")
            print("="*50 + "\n")
        except Exception as e:
            print(f"[NODE-4:DEBUG] Lỗi khi in dữ liệu đầu vào: {e}")

        # Cache logic (giữ nguyên)
        h = self._hash_raw_result(raw_result, instruction)
        cached = self.cache.get(h)
        if cached:
            # ... (phần cache hit giữ nguyên)
            self.metrics.increment("node4.cache_hit")
            return cached

        self.metrics.increment("node4.cache_miss")
        duration = time.perf_counter() - started_at
        self.metrics.observe_latency("node4.latency", duration)
        print(f"[NODE-4:FORMAT] cache miss, start LLM generation. duration_ms={duration * 1000:.1f}")

        # 2. CHUẨN BỊ PROMPT
        prompt = self._build_formatter_prompt(raw_result, instruction)
        print(f"[NODE-4:FORMAT] Prompt gửi cho LLM:\n{prompt[:500]}...") # In 500 ký tự đầu của prompt

        try:
            # Gọi LLM
            gen = await self.llm.generate(
                prompt,
                max_tokens=NODE4_GENERATE_MAX_TOKENS,
                temperature=NODE4_GENERATE_TEMPERATURE,
                timeout=NODE4_TIMEOUT,
                top_p=NODE4_GENERATE_TOP_P,
                repeat_penalty=NODE4_REPEAT_PENALTY,
                stop=["<|im_end|>"]
            )

            # Kiểm tra kết quả LLM trả về
            if not gen:
                raise ValueError("LLM trả về kết quả rỗng (None/Empty)")

            text = (gen.get('text') or str(gen)).strip()

            # Nếu LLM trả về nhưng nội dung vô nghĩa
            if not text:
                 raise ValueError("LLM trả về dictionary nhưng trường 'text' bị trống")

            self.metrics.increment("node4.llm_success")
            print(f"[NODE-4:FORMAT] LLM phản hồi thành công. Output: {text[:160]}...")

        except LLMCircuitOpenError:
            self.metrics.increment("node4.circuit_open")
            text = "⚠️ Hệ thống tạm bận (Circuit Open). Dữ liệu thô: " + str(raw_result)[:200]
            print("[NODE-4:FORMAT] Lỗi: Circuit Breaker đang mở.")

        except Exception as exc:
            # 3. NÉM LỖI CỤ THỂ VÀ TRACEBACK
            self.metrics.increment("node4.fallback")

            # Lấy chi tiết lỗi kèm dòng code bị lỗi
            error_detail = traceback.format_exc()

            print("\n" + "!"*50)
            print(f"[NODE-4:CRITICAL_ERROR] Đã xảy ra lỗi tại Node 4!")
            print(f"Chi tiết lỗi: {str(exc)}")
            print(f"Stack Trace:\n{error_detail}")
            print("!"*50 + "\n")

            # Trả về lỗi cụ thể lên UI để Dũng nhìn thấy luôn trên trình duyệt
            text = f"❌ Lỗi Node 4: {type(exc).__name__} - {str(exc)}"

        self.cache.set(h, text)
        duration = time.perf_counter() - started_at
        print(f"[NODE-4:FORMAT] Hoàn thành trong {duration * 1000:.1f}ms")
        return text

    async def handle(
        self,
        user_text: str,
        student_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        handle_started_at = time.perf_counter()
        print(
            f"[ORCH] start query={self._preview(user_text, 120)} student_id={student_id} "
            f"conversation_id={conversation_id}"
        )
        # node 1 split
        segments = await self.node1_query_splitter(user_text)
        print(f"[ORCH] node1_done segments={len(segments)} segments_preview={self._preview(segments, 160)}")
        results = []
        for idx, seg in enumerate(segments, start=1):
            print(f"[ORCH] segment_start index={idx}/{len(segments)} text={self._preview(seg, 120)}")
            # node 2 intent
            intent_info = await self.node2_intent_router(seg)
            intent = intent_info.get('intent')
            if not intent or intent == 'unknown':
                self.metrics.increment("tools.skipped_unknown_intent")
                res = {'message': 'No tool mapped for unknown intent', 'items': []}
                print(f"[NODE-3:TOOLS] index={idx} skipped reason=unknown_intent")
            else:
                try:
                    tool_started_at = time.perf_counter()
                    print(f"[NODE-3:TOOLS] index={idx} intent={intent} action=call")
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
                    self.metrics.increment(f"tools.{intent}.success")
                    tool_duration = time.perf_counter() - tool_started_at
                    self.metrics.observe_latency(f"tools.{intent}.latency", tool_duration)
                    print(
                        f"[NODE-3:TOOLS] index={idx} intent={intent} status=success "
                        f"duration_ms={tool_duration * 1000:.1f} result_preview={self._preview(res, 140)}"
                    )
                    print(f"NODE3 output: {json.dumps(res, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    self.metrics.increment(f"tools.{intent or 'unknown'}.failure")
                    res = {"error": str(e)}
                    print(f"NODE3 output: {json.dumps(res, indent=2, ensure_ascii=False)}")
                    print(f"[NODE-3:TOOLS] index={idx} intent={intent} status=failure error={e}")
            results.append({'segment': seg, 'intent': intent_info, 'raw_result': res})
            print(f"[ORCH] segment_intent index={idx} intent={intent} source={intent_info.get('source')}")
            print("\n" + "="*50)
            print(f"Data from NODE3: {json.dumps(results, indent=2, ensure_ascii=False)}")
            print("="*50 + "\n")

        # node 4 response (generative for all responses as requested)
        formatted = await self.node4_response_formatter(results, "Generate a helpful response in Vietnamese summarizing the search results.")
        summary = self._derive_summary_intent(results)
        parts = [
            {
                "intent": item.get("intent"),
                "text": item.get("segment"),
                "data": item.get("raw_result"),
            }
            for item in results
        ]
        total_duration = time.perf_counter() - handle_started_at
        print(
            f"[ORCH] done intent={summary['intent']} confidence={summary['confidence_label']} "
            f"is_compound={summary['is_compound']} duration_ms={total_duration * 1000:.1f}"
        )
        # Backward-compatible fields: raw + response. New normalized fields are added for route/schema alignment.
        return {
            "raw": results,
            "response": formatted,
            "text": formatted,
            "intent": summary["intent"],
            "confidence": summary["confidence_label"],
            "confidence_score": summary["confidence"],
            "is_compound": summary["is_compound"],
            "parts": parts,
        }
