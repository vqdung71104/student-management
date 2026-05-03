"""
agent_graph.py — LangGraph StateGraph definition + async runner.
"""
from __future__ import annotations
import asyncio
import os
import time
from typing import Any, Dict, Literal, Optional

from app.agents.graph_state import AgentState
from app.agents.graph_nodes import (
    query_splitter_node, intent_router_node, constraint_parser_node, tool_executor_node,
    agent_filter_node, response_formatter_node, synthesize_formatter_node, rule_based_fallback_node,
    _accumulate_and_route_node,
)

try:
    from langgraph.graph import StateGraph, END
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False

GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))

def route_decision(state: AgentState) -> Literal["agent_path", "rule_based_path"]:
    return "agent_path" if state.get("needs_agent") else "rule_based_path"

def should_filter(state: AgentState) -> Literal["filter", "skip_filter"]:
    return "filter" if state.get("needs_agent_filter") else "skip_filter"

def should_continue_loop(state: AgentState) -> Literal["continue_loop", "synthesize_or_end"]:
    segments = state.get("segments", [])
    idx = state.get("current_segment_index", 0)
    return "continue_loop" if idx < len(segments) else "synthesize_or_end"

def should_synthesize(state: AgentState) -> Literal["synthesize", "skip_synthesize"]:
    return "synthesize" if len(state.get("segments", [])) >= 2 else "skip_synthesize"

def _build_graph() -> Optional["StateGraph"]:
    if not _LANGGRAPH_AVAILABLE: return None
    graph = StateGraph(AgentState)

    graph.add_node("query_splitter", query_splitter_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("constraint_parser", constraint_parser_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("agent_filter", agent_filter_node)
    graph.add_node("formatter", response_formatter_node)
    graph.add_node("accumulate", _accumulate_and_route_node)
    graph.add_node("synthesize", synthesize_formatter_node)
    graph.add_node("rule_based_fallback", rule_based_fallback_node)

    graph.set_entry_point("query_splitter")
    graph.add_edge("query_splitter", "intent_router")
    graph.add_conditional_edges("intent_router", route_decision, {"rule_based_path": "tool_executor", "agent_path": "constraint_parser"})
    graph.add_edge("constraint_parser", "tool_executor")
    graph.add_conditional_edges("tool_executor", should_filter, {"filter": "agent_filter", "skip_filter": "formatter"})
    graph.add_edge("agent_filter", "formatter")
    graph.add_edge("formatter", "accumulate")
    graph.add_conditional_edges("accumulate", should_continue_loop, {"continue_loop": "intent_router", "synthesize_or_end": "synthesize"})
    graph.add_conditional_edges("synthesize", should_synthesize, {"synthesize": "synthesize", "skip_synthesize": END})
    graph.add_edge("rule_based_fallback", "formatter")

    return graph

_compiled_graph = None
def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None: _compiled_graph = _build_graph().compile()
    return _compiled_graph

async def run_graph(user_text: str, student_id: Optional[int] = None, conversation_id: Optional[int] = None) -> AgentState:
    compiled = get_compiled_graph()
    initial_state = {
        "user_text": user_text,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "current_segment_index": 0,
        "segment_results": [], # Khởi tạo danh sách rỗng để bắt đầu tích lũy
        "node_trace": []
    }
    try:
        return await asyncio.wait_for(compiled.ainvoke(initial_state), timeout=GLOBAL_TIMEOUT)
    except asyncio.TimeoutError:
        initial_state["error"] = "Timeout"
        return initial_state

async def run_graph_for_orchestrator(user_text: str, student_id: Optional[int] = None, conversation_id: Optional[int] = None) -> dict:
    state = await run_graph(user_text, student_id, conversation_id)
    return {
        "raw": state.get("segment_results", []),
        "response": state.get("synthesized_response") or state.get("final_response") or "OK",
        "text": state.get("synthesized_response") or state.get("final_response") or "OK",
        "intent": state.get("intent", "unknown"),
        "confidence": "high",
        "confidence_score": 1.0,
        "is_compound": len(state.get("segments", [])) > 1,
        "parts": state.get("segment_results", []),
        "debug": {"node_trace": state.get("node_trace", [])}
    }