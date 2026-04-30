"""
Agent Orchestrator — Evaluation & Context Extraction Script
==========================================================

Mục đích:
    Chạy tự động các câu hỏi mẫu, bỏ qua Node-1 (LLM split),
    trích xuất raw data từ Node-3 và response từ Node-4,
    lưu vào evaluation_context.json để đánh giá mô hình fine-tuned.

Điểm khác biệt so với phiên bản trước:
    • Bỏ qua hoàn toàn Node-1 (không gọi LLM split, tránh lỗi localhost:7860).
      Mỗi câu hỏi được xử lý như một query đơn: segments = [query].
    • Tự động load AGENT_INTERNAL_TOOL_KEY từ backend/.env.
    • Đảm bảo header X-Agent-Internal-Key được gửi đúng trong mọi tool call.
    • Vẫn gọi Node-2 (TF-IDF intent routing) và Node-3 (tools) + Node-4 (formatter).
    • Luôn trích xuất raw_result từ Node-3 vào evaluation_context.json.

Cách dùng:
    cd d:/student-management/backend
    python -m scripts.evaluate_orchestrator

Đầu ra:
    evaluation_context.json — danh sách entry, mỗi entry gồm:
        query                   : câu hỏi đầu vào
        raw_context_after_node3 : danh sách raw_result sau Node-3 (chưa qua LLM)
        api_response_node4      : response sau Node-4 (đã format)
        intent_detected         : intent được phát hiện (Node-2)
        node3_subtype           : subtype của Node-3 (3a / 3b / 3c)
        tool_errors             : danh sách lỗi từ tool (nếu có)
        is_tool_error           : True nếu có bất kỳ lỗi tool nào
        duration_ms             : tổng thời gian xử lý
        error                   : lỗi unexpected (None nếu thành công)
        model_used              : model LLM dùng ở Node-4
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Paths ────────────────────────────────────────────────────────────────────
BACKEND_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BACKEND_ROOT))


# ── Load .env variables (backend/.env) ────────────────────────────────────────
def _load_env_from_file(env_path: Path) -> None:
    """Read backend/.env and set os.environ for all VAR=VALUE lines."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Only set if not already in environment (env takes precedence)
        if key not in os.environ:
            os.environ[key] = value


_dotenv_path = BACKEND_ROOT / ".env"
_load_env_from_file(_dotenv_path)
_dotenv_example = BACKEND_ROOT / ".env.example"
_load_env_from_file(_dotenv_example)


# ── Env vars used by this script ──────────────────────────────────────────────
STUDENT_ID = int(os.environ.get("EVAL_STUDENT_ID", "1"))
CONVERSATION_ID = int(os.environ.get("EVAL_CONVERSATION_ID", "1"))
AGENT_INTERNAL_KEY = os.environ.get(
    "AGENT_INTERNAL_TOOL_KEY",
    os.environ.get("AGENT_INTERNAL_KEY", "dev-agent-key"),
)


# ── Test queries ──────────────────────────────────────────────────────────────
EVAL_QUERIES: List[str] = [
    "Tôi nên đăng ký lớp nào kỳ sau?",
    "Tôi nên đăng ký học phần nào kỳ sau?",
    "Thông tin học phần Cơ sở dữ liệu",
    "Thông tin học phần Giải tích 2",
    "Thông tin học phần Sinh học đại cương",
    "Thông tin lớp 168234",
    "Thông tin lớp 166126",
    "Điểm CPA của tôi",
    "GPA kỳ 2024.1",
    "Điểm môn Giải tích 1",
    "Thông tin về tôi",
]


# ── JSON serializer ───────────────────────────────────────────────────────────
def _serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize any object to JSON-compatible Python type.
    Handles Pydantic v1/v2 models, datetime, bytes, dataclasses, etc.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_serialize_for_json(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): _serialize_for_json(v) for k, v in obj.items()}
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return _serialize_for_json(obj.model_dump())
    # Pydantic v1 / attrs
    if hasattr(obj, "dict"):
        return _serialize_for_json(obj.dict())
    if hasattr(obj, "__dict__"):
        return _serialize_for_json(obj.__dict__)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


# ── Dataclass ─────────────────────────────────────────────────────────────────
@dataclass
class EvaluationEntry:
    query: str
    raw_context_after_node3: List[Dict[str, Any]] = field(default_factory=list)
    api_response_node4: str = ""
    intent_detected: Optional[str] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    node3_subtypes: List[Optional[str]] = field(default_factory=list)
    duration_ms: float = 0.0
    model_used: Optional[str] = None
    from_cache: bool = False
    error: Optional[str] = None
    is_tool_error: bool = False
    tool_errors: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Core: run single query bypassing Node-1 ───────────────────────────────────
async def run_single_query(
    orchestrator,
    query: str,
    student_id: int,
    conversation_id: int,
) -> EvaluationEntry:
    """
    Simulate orchestrator flow WITHOUT Node-1:

        bypass Node-1 → segments = [query]
        Node-2        → orchestrator.node2_intent_router(query)
        Node-3        → orchestrator.tools.call(intent, payload)
        Node-4        → orchestrator.node4_response_formatter(results, ...)

    Always returns an EvaluationEntry — even on error.
    """
    entry = EvaluationEntry(query=query)
    started = time.perf_counter()

    # ── Bypass Node-1 ───────────────────────────────────────────────────────────
    # Each query is treated as a single-segment query.
    segments = [query]
    print(f"[BYPASS-NODE1] query={query[:60]}")

    results: List[Dict[str, Any]] = []

    for seg_idx, seg in enumerate(segments, start=1):
        print(f"[NODE-2] segment {seg_idx}/{len(segments)}: {seg[:80]}")

        # ── Node-2: Intent routing (TF-IDF only — no LLM call) ─────────────────
        try:
            intent_info = await orchestrator.node2_intent_router(seg)
        except Exception as exc:
            intent_info = {"intent": "unknown", "confidence": 0.0, "source": "error"}
            print(f"[NODE-2] ERROR: {type(exc).__name__}: {exc}")

        intent = intent_info.get("intent") if isinstance(intent_info, dict) else "unknown"

        # ── Guard: skip greeting / thanks / unknown intents ───────────────────
        _SKIP_INTENTS = frozenset({"greeting", "thanks", "unknown", None, ""})
        if intent in _SKIP_INTENTS:
            orchestrator.metrics.increment("tools.skipped_greeting_intent")
            greeting = (
                "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. "
                "Mình có thể giúp gì cho bạn?"
            )
            results.append({
                "segment": seg,
                "intent": intent_info,
                "raw_result": {"status": "success", "data": greeting},
                "node3_subtype": None,
            })
            continue

        # ── Resolve Node-3 subtype ─────────────────────────────────────────────
        node3_subtype = orchestrator._resolve_node3_subtype(intent)

        # ── Node-3: Tool call ──────────────────────────────────────────────────
        if not intent or intent == "unknown":
            orchestrator.metrics.increment("tools.skipped_unknown_intent")
            res: Dict[str, Any] = {"status": "success", "data": [], "message": "No tool mapped"}
        else:
            payload = {
                "q": seg,
                "student_id": student_id,
                "conversation_id": conversation_id,
            }
            tool_started = time.perf_counter()
            try:
                # tools.call() returns structured dict (never raises on HTTP errors)
                res = await orchestrator.tools.call(intent, payload)
                tool_duration = (time.perf_counter() - tool_started) * 1000
                orchestrator.metrics.increment(f"tools.{intent}.success")
                print(
                    f"[NODE-3][{node3_subtype or '?'}] intent={intent} "
                    f"done in {tool_duration:.1f}ms"
                )
            except Exception as exc:
                orchestrator.metrics.increment(f"tools.{intent or 'unknown'}.failure")
                err_msg = f"TOOLS_LAYER_UNEXPECTED: {type(exc).__name__}: {exc}"
                print(f"[NODE-3] UNEXPECTED [{node3_subtype or '?'}] intent={intent}: {exc}")
                res = {"status": "error", "error": err_msg}

        results.append({
            "segment": seg,
            "intent": intent_info,
            "raw_result": res,
            "node3_subtype": node3_subtype,
        })

    # ── Node-4: Response formatter ───────────────────────────────────────────────
    node4_started = time.perf_counter()
    try:
        node4_result = await orchestrator.node4_response_formatter(
            results,
            "Generate response",
            original_query=query,
            intent_hints=[r.get("intent", {}).get("intent") if isinstance(r.get("intent"), dict) else r.get("intent") for r in results],
        )
    except Exception as exc:
        node4_result = {
            "text": f"[Node-4 ERROR] {type(exc).__name__}: {exc}",
            "model_used": "error",
            "processing_time_ms": 0,
            "from_cache": False,
        }
        print(f"[NODE-4] ERROR: {type(exc).__name__}: {exc}")

    elapsed = (time.perf_counter() - started) * 1000
    entry.duration_ms = round(elapsed, 2)

    # ── Populate entry fields ───────────────────────────────────────────────────
    entry.raw_context_after_node3 = _serialize_for_json(results)

    # Detect structured tool errors
    tool_errors: List[Dict[str, Any]] = []
    for raw_item in results:
        raw_result = raw_item.get("raw_result") or {}
        if isinstance(raw_result, dict) and raw_result.get("status") == "error":
            tool_errors.append(raw_result)
    entry.tool_errors = tool_errors
    entry.is_tool_error = bool(tool_errors)

    entry.api_response_node4 = node4_result.get("text") or ""
    entry.intent_detected = next(
        (r.get("intent", {}).get("intent") if isinstance(r.get("intent"), dict) else r.get("intent"))
        for r in results if r.get("intent")
    ) or None
    entry.confidence_score = next(
        (r.get("intent", {}).get("confidence") if isinstance(r.get("intent"), dict) else None)
        for r in results if r.get("intent")
    )
    entry.node3_subtypes = _serialize_for_json([r.get("node3_subtype") for r in results])
    entry.model_used = node4_result.get("model_used")
    entry.from_cache = node4_result.get("from_cache", False)

    # ── Console output ───────────────────────────────────────────────────────────
    if tool_errors:
        primary_err = tool_errors[0]
        err_msg = primary_err.get("error", "") or ""
        err_category = err_msg.split(":")[0] if ":" in err_msg else err_msg[:30]
        print(
            f"  🔒 [{entry.intent_detected or '?'}] [{err_category}] "
            f"duration={entry.duration_ms:.0f}ms"
        )
    else:
        print(
            f"  ✅ [{entry.intent_detected or '?'}] "
            f"model={entry.model_used or '-'} "
            f"duration={entry.duration_ms:.0f}ms"
        )

    return entry


# ── Run all queries ────────────────────────────────────────────────────────────
async def run_evaluation(
    queries: List[str],
    student_id: int,
    conversation_id: int,
    output_path: str,
) -> List[EvaluationEntry]:
    """
    Instantiate orchestrator, run all queries, extract context, save JSON.
    """
    print("[INIT] Importing AgentOrchestrator...")
    from app.agents.agent_orchestrator import AgentOrchestrator

    # ── Set the module-level key BEFORE creating any ToolsRegistry instance ──────
    # This is the variable that ToolsRegistry.__init__ reads to build _default_headers.
    from app.agents import tools_registry as tr

    tr.AGENT_INTERNAL_TOOL_KEY = AGENT_INTERNAL_KEY

    orchestrator = AgentOrchestrator()

    # ── Inject headers directly into the tools instance ──────────────────────────
    # _default_headers is an instance attribute (set in __init__), so we patch it here.
    orchestrator.tools._default_headers = {
        "X-Agent-Internal-Key": AGENT_INTERNAL_KEY
    }

    print(f"[INIT] Orchestrator ready.")
    print(f"       AGENT_INTERNAL_TOOL_KEY = {AGENT_INTERNAL_KEY!r}")
    print(f"       backend root            = {BACKEND_ROOT}")
    print(f"       student_id              = {student_id}")
    print(f"       conversation_id         = {conversation_id}\n")

    results: List[EvaluationEntry] = []
    total_started = time.perf_counter()

    for i, query in enumerate(queries, start=1):
        print(f"[{i}/{len(queries)}] {query[:60]}{'...' if len(query) > 60 else ''}")
        entry = await run_single_query(orchestrator, query, student_id, conversation_id)
        results.append(entry)
        # Brief pause between queries to avoid overwhelming the backend
        await asyncio.sleep(0.3)

    total_elapsed = (time.perf_counter() - total_started) * 1000

    # ── Save JSON ──────────────────────────────────────────────────────────────
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_queries": len(queries),
            "student_id": student_id,
            "conversation_id": conversation_id,
            "total_duration_ms": round(total_elapsed, 2),
            "script_version": "2.0.0",
            "node1_bypass": True,
            "agent_internal_key_used": AGENT_INTERNAL_KEY,
            "description": (
                "Evaluation context for fine-tuned LLM comparison on Google Colab. "
                "raw_context_after_node3 = raw tool output (input cho LLM fine-tuned). "
                "api_response_node4  = baseline response from current system. "
                "tool_errors         = HTTP/API errors if any (HTTP_403_AUTH, TIMEOUT, ...)."
            ),
        },
        "results": [r.to_dict() for r in results],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # ── Print summary ───────────────────────────────────────────────────────────
    tool_failures = [r for r in results if r.is_tool_error]
    auth_failures = [
        r for r in tool_failures
        if any("AUTH" in str(e.get("error", "")) for e in r.tool_errors)
    ]
    success_with_data = [r for r in results if not r.error and not r.is_tool_error]

    print(f"\n{'='*60}")
    print(f"Evaluation complete:")
    print(f"  ✅ Real data retrieved  : {len(success_with_data)}/{len(results)}")
    print(f"  🔒 Auth errors (403/401): {len(auth_failures)}")
    print(f"  ⚠️  Other tool errors    : {len(tool_failures) - len(auth_failures)}")
    print(f"  Total duration          : {total_elapsed:.0f}ms")
    print(f"  Output                  : {output_path}")

    if auth_failures:
        print(f"\n  ⚠️  AUTHENTICATION FAILURES detected:")
        for r in auth_failures:
            err = r.tool_errors[0] if r.tool_errors else {}
            print(f"    • [{r.query[:50]}] → {err.get('error', '')[:80]}")
        print(f"\n  → Fix: Set AGENT_INTERNAL_TOOL_KEY in backend/.env to match")
        print(f"    the value in agent_tool_routes.py (_verify_internal_key).")
        print(f"    Example: AGENT_INTERNAL_TOOL_KEY=dev-agent-key")

    return results


# ── Entry point ────────────────────────────────────────────────────────────────
async def main():
    output_path = BACKEND_ROOT / "evaluation_context.json"

    print(f"Backend root          : {BACKEND_ROOT}")
    print(f"Output file           : {output_path}")
    print(f"Queries               : {len(EVAL_QUERIES)}")
    print(f"Student ID            : {STUDENT_ID}")
    print(f"Conversation ID       : {CONVERSATION_ID}")
    print(f"Agent Key loaded from : AGENT_INTERNAL_TOOL_KEY = {AGENT_INTERNAL_KEY!r}")
    print(f"\n{'='*60}\n")

    results = await run_evaluation(
        queries=EVAL_QUERIES,
        student_id=STUDENT_ID,
        conversation_id=CONVERSATION_ID,
        output_path=str(output_path),
    )

    # ── Summary table ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"{'#':<3} {'Query (truncated)':<45} {'Intent':<28} {'Status':<30} {'ms'}")
    print(f"{'-'*60}")
    for i, r in enumerate(results, start=1):
        q_trunc = r.query[:42] + "..." if len(r.query) > 42 else r.query
        if r.is_tool_error:
            err = r.tool_errors[0] if r.tool_errors else {}
            err_msg = err.get("error", "") or "-"
            status = err_msg.split(":")[0] if ":" in err_msg else err_msg[:30]
            icon = "🔒" if "AUTH" in err_msg else "⚠️"
        elif r.error:
            status = r.error[:30]
            icon = "💥"
        else:
            status = r.model_used or "-"
            icon = "✅"
        intent = r.intent_detected or "-"
        print(f"{icon}{i:<2} {q_trunc:<45} {intent:<28} {status:<30} {r.duration_ms:.0f}")
    print(f"{'-'*60}")

    # ── Preview first real-data entry ──────────────────────────────────────────
    first_real = next(
        (r for r in results if r.raw_context_after_node3 and not r.is_tool_error),
        None,
    )
    if first_real:
        preview = json.dumps(
            first_real.raw_context_after_node3,
            ensure_ascii=False,
            indent=2,
        )[:1000]
        print(f"\nPreview raw_context (first real-data query):\n{preview}...")
    else:
        print("\n⚠ No queries returned real data — check tool_errors above.")


if __name__ == "__main__":
    asyncio.run(main())
