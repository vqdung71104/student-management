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

LLM_REASONING_TIMEOUT = float(os.environ.get("LLM_REASONING_TIMEOUT", "5.0"))
TOOL_EXECUTION_TIMEOUT = float(os.environ.get("TOOL_EXECUTION_TIMEOUT", "10.0"))
GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "25.0"))

def route_decision(state: AgentState) -> Literal["agent_path", "rule_based_path", "fallback_path"]:
    if state.get("reasoning_fallback"):
        return "fallback_path"
    return "agent_path" if state.get("needs_agent") else "rule_based_path"

def should_filter(state: AgentState) -> Literal["filter", "skip_filter"]:
    return "filter" if state.get("needs_agent_filter") else "skip_filter"

def next_after_accumulate(state: AgentState) -> Literal["continue_loop", "synthesize", "end"]:
    segments = state.get("segments", [])
    idx = state.get("current_segment_index", 0)
    if idx < len(segments):
        return "continue_loop"
    return "synthesize" if len(segments) >= 2 else "end"

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
    graph.add_conditional_edges(
        "intent_router",
        route_decision,
        {
            "rule_based_path": "tool_executor",
            "agent_path": "constraint_parser",
            "fallback_path": "rule_based_fallback",
        },
    )
    graph.add_edge("constraint_parser", "tool_executor")
    graph.add_conditional_edges("tool_executor", should_filter, {"filter": "agent_filter", "skip_filter": "formatter"})
    graph.add_edge("agent_filter", "formatter")
    graph.add_edge("formatter", "accumulate")
    graph.add_conditional_edges(
        "accumulate",
        next_after_accumulate,
        {
            "continue_loop": "intent_router",
            "synthesize": "synthesize",
            "end": END,
        },
    )
    graph.add_edge("synthesize", END)
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

async def run_graph_for_orchestrator(
    user_text: str, 
    student_id: Optional[int] = None, 
    conversation_id: Optional[int] = None
) -> dict:
    state = await run_graph(user_text, student_id, conversation_id)
    
    if state.get("error") == "Timeout":
        raise asyncio.TimeoutError("LangGraph orchestration timed out")

    # --- LOGIC LẤY PHẢN HỒI THÔNG MINH ---
    # 1. Ưu tiên kết quả tổng hợp (Synthesized) hoặc kết quả cuối cùng (Final)
    final_txt = state.get("synthesized_response") or state.get("final_response")

    # 2. Nếu vẫn chưa có (thường do chạy song song hoặc lỗi formatter), 
    #    duyệt qua từng segment_results để nối văn bản đã format
    if not final_txt or final_txt == "OK":
        segment_results = state.get("segment_results", [])
        if segment_results:
            parts = []
            for res in segment_results:
                # Lấy text từ formatted_text (nếu bạn đã lưu ở bước accumulate) 
                # hoặc bóc trực tiếp từ raw_result
                seg_formatted = res.get("formatted_text")
                if seg_formatted:
                    parts.append(seg_formatted)
                else:
                    raw = res.get("raw_result")
                    if isinstance(raw, dict):
                        # Bóc tách linh hoạt cấu trúc dữ liệu từ Backend
                        text_data = raw.get("text") or (raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}).get("text")
                        if text_data:
                            parts.append(text_data)
            
            if parts:
                final_txt = "\n\n---\n\n".join(parts)

    # 3. Chốt hạ: Không bao giờ để hiện chữ "OK"
    if not final_txt or final_txt == "OK":
        final_txt = "Mình đã xử lý xong yêu cầu của bạn, bạn hãy kiểm tra kết quả bên dưới nhé."

    return {
        "raw": state.get("segment_results", []),
        "response": final_txt,
        "text": final_txt,
        "intent": state.get("intent", "unknown"),
        "confidence": "high",
        "confidence_score": 1.0,
        "is_compound": len(state.get("segments", [])) > 1,
        "parts": state.get("segment_results", []),
        "debug": {"node_trace": state.get("node_trace", [])}
    }
