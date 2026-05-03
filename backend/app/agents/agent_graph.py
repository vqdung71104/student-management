"""
agent_graph.py — LangGraph StateGraph definition + async runner.

Kiến trúc Hybrid với Multi-Segment Fan-Out:

    query_splitter_node (trả về segments[])
          │
          ▼
    intent_router_node (trả về intent, confidence, constraints, clean_query cho segment 0)
          │
          ▼
    ┌─────────────────────────────────┐
    │  Fan-out: Send per segment      │
    │  "process_segment"              │
    │    intent_router                 │
    │    constraint_parser             │
    │    tool_executor                │
    │    agent_filter (bắt buộc nếu  │
    │              subject_reg)        │
    │    response_formatter            │
    │    accumulate → segment_results  │
    └─────────────────────────────────┘
          │
          ▼
    synthesize_formatter_node
    (tổng hợp TẤT CẢ segment_results)
          │
          ▼
         END

Conditional edges:
  - route_decision: needs_agent=True → agent_path, else → rule_based_path
  - should_filter: always for subject_registration OR if constraints exist
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, Literal, Optional

from app.agents.graph_state import AgentState
from app.agents.graph_nodes import (
    query_splitter_node,
    intent_router_node,
    constraint_parser_node,
    tool_executor_node,
    agent_filter_node,
    response_formatter_node,
    synthesize_formatter_node,
    rule_based_fallback_node,
    _get_llm,
    _get_tools,
    _get_cache,
    _is_complex_query,
    _resolve_node3_subtype,
    _compact_data,
    check_fallback,
)

# ──────────────────────────────────────────────────────────────────────────────
# Lazy import — avoids crash if langgraph is not installed
# ──────────────────────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langgraph.constants import Send
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore[assignment, misc]
    END = None  # type: ignore[misc, assignment]
    Send = None  # type: ignore[assignment, misc]

GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "10.0"))

# ──────────────────────────────────────────────────────────────────────────────
# Conditional edge functions
# ──────────────────────────────────────────────────────────────────────────────

def route_decision(state: AgentState) -> Literal["agent_path", "rule_based_path"]:
    """
    Quyết định nhánh xử lý dựa trên needs_agent flag từ intent_router.
    - needs_agent=False → rule_based_path (TF-IDF cao, không có constraint keywords)
    - needs_agent=True  → agent_path (có constraint keywords hoặc LLM fallback)
    """
    needs_agent = state.get("needs_agent", False)
    intent = state.get("intent", "unknown")

    if needs_agent:
        print(f"[GRAPH:route] intent={intent} → AGENT_PATH (complex/constrained query)")
        return "agent_path"
    else:
        print(f"[GRAPH:route] intent={intent} → RULE_BASED_PATH (simple query)")
        return "rule_based_path"


def should_filter(state: AgentState) -> Literal["filter", "skip_filter"]:
    """
    Quyết định xem có chạy agent_filter không:
      - ALWAYS filter cho subject_registration_suggestion (bắt buộc theo yêu cầu kỹ thuật)
      - Filter nếu có constraints thực tế (exclude_subjects, forbidden_time_slots, ...)
      - Skip nếu không có constraints
    """
    intent = state.get("intent", "")
    constraints = state.get("constraints") or {}
    needs_agent_filter = state.get("needs_agent_filter", False)

    # Bắt buộc filter cho subject_registration_suggestion
    if intent == "subject_registration_suggestion":
        print("[GRAPH:filter] subject_registration → FORCE FILTER")
        return "filter"

    # Filter nếu có bất kỳ constraint nào
    if needs_agent_filter:
        print("[GRAPH:filter] has constraints → FILTER")
        return "filter"

    # Skip nếu không có constraints
    has_constraints = any(
        constraints.get(k)
        for k in ("exclude_subjects", "forbidden_time_slots", "forbidden_times", "days")
        if constraints.get(k)
    )
    if has_constraints:
        print("[GRAPH:filter] has constraints → FILTER")
        return "filter"

    print("[GRAPH:filter] no constraints → SKIP")
    return "skip_filter"


def check_fallback(state: AgentState) -> Literal["formatter_done", "fallback"]:
    """
    Sau formatter, kiểm tra xem có lỗi timeout/error không để quyết định fallback.
    """
    if state.get("used_fallback") or state.get("error"):
        print("[GRAPH:fallback] detected → fallback_path")
        return "fallback"
    print("[GRAPH:fallback] no error → END")
    return "formatter_done"


def should_synthesize(state: AgentState) -> Literal["synthesize", "skip_synthesize"]:
    """
    Chỉ tổng hợp khi có >= 2 segment.
    """
    n = len(state.get("segment_results", []))
    if n >= 2:
        print(f"[GRAPH:synthesize] {n} segments → SYNTHESIZE")
        return "synthesize"
    print(f"[GRAPH:synthesize] {n} segment(s) → SKIP SYNTHESIZE")
    return "skip_synthesize"


# ──────────────────────────────────────────────────────────────────────────────
# Fan-out: process each segment as a separate subgraph
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# Graph builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_graph() -> Optional["StateGraph"]:
    if not _LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(AgentState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node("query_splitter", query_splitter_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("constraint_parser", constraint_parser_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("agent_filter", agent_filter_node)
    graph.add_node("formatter", response_formatter_node)
    graph.add_node("synthesize", synthesize_formatter_node)
    graph.add_node("rule_based_fallback", rule_based_fallback_node)

    # ── Entry point ─────────────────────────────────────────────────────────
    graph.set_entry_point("query_splitter")

    # ── query_splitter → intent_router ──────────────────────────────────────
    graph.add_edge("query_splitter", "intent_router")

    # ── intent_router → route_decision ─────────────────────────────────────
    graph.add_conditional_edges(
        "intent_router",
        route_decision,
        {
            "rule_based_path": "tool_executor",
            "agent_path": "constraint_parser",
        },
    )

    # ── agent_path: check for error/timeout → fallback OR continue ────────────────
    # If graph already detected an error (e.g. outer timeout before entering agent_path),
    # skip agent logic and go straight to rule-based fallback.
    graph.add_conditional_edges(
        "constraint_parser",
        check_fallback,
        {
            "fallback": "rule_based_fallback",
            "formatter_done": "tool_executor",
        },
    )

    # ── tool_executor → should_filter ───────────────────────────────────────
    graph.add_conditional_edges(
        "tool_executor",
        should_filter,
        {
            "filter": "agent_filter",
            "skip_filter": "formatter",
        },
    )

    # ── agent_filter → formatter ───────────────────────────────────────────
    graph.add_edge("agent_filter", "formatter")

    # ── rule_based_path: tool_executor → formatter ───────────────────────────
    graph.add_edge("tool_executor", "formatter")

    # ── formatter → synthesize decision ─────────────────────────────────────
    graph.add_conditional_edges(
        "formatter",
        should_synthesize,
        {
            "synthesize": "synthesize",
            "skip_synthesize": END,
        },
    )

    # ── synthesize → END ───────────────────────────────────────────────────
    graph.add_edge("synthesize", END)

    # ── rule_based_fallback ────────────────────────────────────────────────
    graph.add_edge("rule_based_fallback", "formatter")

    return graph


# Singleton compiled graph
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        builder = _build_graph()
        if builder is not None:
            _compiled_graph = builder.compile()
        else:
            raise RuntimeError(
                "LangGraph is not installed. "
                "Run: pip install langgraph langgraph-sdk; "
                "then update backend/requirements.txt"
            )
    return _compiled_graph


# ──────────────────────────────────────────────────────────────────────────────
# Async runner
# ──────────────────────────────────────────────────────────────────────────────

async def run_graph(
    user_text: str,
    student_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> AgentState:
    """
    Chạy LangGraph với GLOBAL_TIMEOUT.
    Nếu vượt quá 10s, bắt asyncio.TimeoutError và trả về state với fallback_reason.
    """
    compiled = get_compiled_graph()

    initial_state: AgentState = {
        "user_text": user_text,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "segments": [],
        "current_segment_index": 0,
        "intent": None,
        "confidence": 0.0,
        "intent_source": None,
        "is_complex": False,
        "needs_agent": False,
        "constraints": None,
        "clean_query": None,
        "raw_data": None,
        "filtered_data": None,
        "needs_agent_filter": False,
        "segment_results": [],
        "final_response": None,
        "formatted_result": None,
        "error": None,
        "fallback_reason": None,
        "used_fallback": False,
        "node_trace": [],
        "metadata": {},
    }

    try:
        result = await asyncio.wait_for(
            compiled.ainvoke(initial_state),
            timeout=GLOBAL_TIMEOUT,
        )
        return result

    except asyncio.TimeoutError:
        print(f"[GRAPH] TIMEOUT after {GLOBAL_TIMEOUT}s → marking fallback")
        initial_state["error"] = f"Graph execution timed out after {GLOBAL_TIMEOUT}s"
        initial_state["fallback_reason"] = "graph_timeout"
        return initial_state


# ──────────────────────────────────────────────────────────────────────────────
# Compatibility wrapper for AgentOrchestrator.handle()
# ──────────────────────────────────────────────────────────────────────────────

async def run_graph_for_orchestrator(
    user_text: str,
    student_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> dict:
    """
    Chạy graph và trả về dict theo format cũ:
    {
        "raw": [...segment_results],
        "response": final_response_text,
        "text": final_response_text,
        "intent": summary_intent,
        ...
    }
    """
    started_at = time.perf_counter()
    state = await run_graph(user_text, student_id, conversation_id)

    final_response = state.get("final_response") or ""
    segment_results = state.get("segment_results", [])
    fallback_reason = state.get("fallback_reason")
    used_fallback = state.get("used_fallback", False)
    node_trace = state.get("node_trace", [])
    formatted_result = state.get("formatted_result") or {}

    # Build summary intent
    if len(segment_results) > 1:
        summary_intent = "compound"
        is_compound = True
        confidence_label = "medium"
        confidence_score = 0.6
    elif segment_results:
        first_intent_info = segment_results[0].get("intent") or {}
        if isinstance(first_intent_info, dict):
            summary_intent = first_intent_info.get("intent", "unknown")
            confidence_score = float(first_intent_info.get("confidence", 0.0))
        else:
            summary_intent = str(first_intent_info) if first_intent_info else "unknown"
            confidence_score = 0.0
        is_compound = False
        confidence_label = (
            "high" if confidence_score >= 0.8
            else "medium" if confidence_score >= 0.5
            else "low"
        )
    else:
        summary_intent = state.get("intent") or "unknown"
        confidence_score = state.get("confidence", 0.0)
        is_compound = False
        confidence_label = (
            "high" if confidence_score >= 0.8
            else "medium" if confidence_score >= 0.5
            else "low"
        )

    # Build parts
    parts = [
        {
            "intent": item.get("intent"),
            "node3_subtype": item.get("node3_subtype"),
            "text": item.get("segment"),
            "data": item.get("raw_result"),
        }
        for item in segment_results
    ]

    total_ms = (time.perf_counter() - started_at) * 1000
    print(f"[GRAPH:RUN] done intent={summary_intent} duration_ms={total_ms:.1f} fallback={used_fallback}")

    return {
        "raw": segment_results,
        "response": final_response,
        "text": final_response,
        "intent": summary_intent,
        "confidence": confidence_label,
        "confidence_score": confidence_score,
        "is_compound": is_compound,
        "parts": parts,
        "debug": {
            "llm_processing_time_ms": formatted_result.get("processing_time_ms"),
            "model_used": formatted_result.get("model_used"),
            "from_cache": formatted_result.get("from_cache", False),
            "node_trace": node_trace,
            "used_fallback": used_fallback,
            "fallback_reason": fallback_reason,
            "is_compound": is_compound,
            "segments": len(segment_results),
            "intents": [
                r.get("intent", {}).get("intent") if isinstance(r.get("intent"), dict) else r.get("intent")
                for r in segment_results
            ],
        },
    }
