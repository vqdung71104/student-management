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
GLOBAL_TIMEOUT = float(os.environ.get("AGENT_REASONING_TIMEOUT", "55.0"))

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

async def _legacy_run_graph_impl(user_text: str, student_id: Optional[int] = None, conversation_id: Optional[int] = None) -> AgentState:
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

async def _legacy_run_graph_for_orchestrator_old(
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


def _extract_part_text(part: Dict[str, Any]) -> str:
    formatted = part.get("formatted_result")
    if isinstance(formatted, dict):
        text = formatted.get("text")
        if isinstance(text, str) and text.strip():
            return text

    seg_formatted = part.get("formatted_text")
    if isinstance(seg_formatted, str) and seg_formatted.strip():
        return seg_formatted

    raw = part.get("raw_result")
    if isinstance(raw, dict):
        raw_text = raw.get("text")
        if isinstance(raw_text, str) and raw_text.strip():
            return raw_text
        payload = raw.get("data")
        if isinstance(payload, dict):
            payload_text = payload.get("text")
            if isinstance(payload_text, str) and payload_text.strip():
                return payload_text
    return ""


def _extract_part_data(part: Dict[str, Any]) -> Any:
    formatted = part.get("formatted_result")
    if isinstance(formatted, dict) and "data" in formatted:
        return formatted.get("data")

    raw = part.get("raw_result")
    if isinstance(raw, dict):
        payload = raw.get("data")
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data")
        if isinstance(payload, list):
            return payload
    return None


def _normalize_part(part: Dict[str, Any]) -> Dict[str, Any]:
    formatted = part.get("formatted_result") if isinstance(part.get("formatted_result"), dict) else {}
    normalized = {
        "segment": part.get("segment"),
        "intent": part.get("intent"),
        "text": _extract_part_text(part),
        "data": _extract_part_data(part),
        "raw": part.get("raw_result"),
        "route": part.get("route"),
    }
    for key in (
        "metadata",
        "question_type",
        "question_options",
        "conversation_state",
        "is_preference_collecting",
        "requires_auth",
        "rule_engine_used",
        "file_url",
        "download_url",
        "excel_url",
        "xlsx_url",
        "export_url",
    ):
        if key in formatted:
            normalized[key] = formatted.get(key)
    return normalized


async def run_graph_for_orchestrator(
    user_text: str,
    student_id: Optional[int] = None,
    conversation_id: Optional[int] = None
) -> dict:
    state = await run_graph(user_text, student_id, conversation_id)

    if state.get("error") == "Timeout":
        raise asyncio.TimeoutError("LangGraph orchestration timed out")

    segment_results = state.get("segment_results", []) or []
    parts = [_normalize_part(part) for part in segment_results]

    final_txt = state.get("synthesized_response") or state.get("final_response")
    if (not final_txt or final_txt == "OK") and parts:
        text_parts = [part.get("text", "").strip() for part in parts if isinstance(part.get("text"), str) and part.get("text").strip()]
        if text_parts:
            final_txt = "\n\n---\n\n".join(text_parts)

    if not final_txt or final_txt == "OK":
        final_txt = "MÃ¬nh Ä‘Ã£ xá»­ lÃ½ xong yÃªu cáº§u cá»§a báº¡n, báº¡n hÃ£y kiá»ƒm tra káº¿t quáº£ bÃªn dÆ°á»›i nhÃ©."

    data_parts = [part.get("data") for part in parts if part.get("data") is not None]
    if len(data_parts) == 1:
        final_data = data_parts[0]
    elif data_parts:
        final_data = data_parts
    else:
        final_data = None

    raw_payload: Any = segment_results
    if parts:
        raw_candidates = [part.get("raw") for part in parts if part.get("raw") is not None]
        if len(raw_candidates) == 1:
            raw_payload = raw_candidates[0]
        elif raw_candidates:
            raw_payload = raw_candidates

    return {
        "raw": raw_payload,
        "response": final_txt,
        "text": final_txt,
        "data": final_data,
        "intent": state.get("intent", "unknown"),
        "confidence": "high",
        "confidence_score": 1.0,
        "is_compound": len(state.get("segments", [])) > 1,
        "parts": parts,
        "debug": {"node_trace": state.get("node_trace", [])}
    }


async def _run_segment_pipeline(
    segment: str,
    all_segments: list[str],
    index: int,
    student_id: Optional[int],
    conversation_id: Optional[int],
) -> Dict[str, Any]:
    state: AgentState = {
        "user_text": segment,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "segments": all_segments,
        "current_segment_index": index,
        "segment_results": [],
        "node_trace": [],
    }

    state.update(await intent_router_node(state))

    if state.get("reasoning_fallback"):
        state.update(rule_based_fallback_node(state))
    else:
        if state.get("needs_agent"):
            state.update(constraint_parser_node(state))
        state.update(await tool_executor_node(state))
        if state.get("needs_agent_filter"):
            state.update(agent_filter_node(state))

    state.update(response_formatter_node(state))
    accumulated = _accumulate_and_route_node(state)
    segment_result = (accumulated.get("segment_results") or [None])[0]
    return segment_result or {}


async def _run_parallel_graph_segments(
    user_text: str,
    segments: list[str],
    student_id: Optional[int],
    conversation_id: Optional[int],
    initial_trace: list[str],
) -> AgentState:
    segment_results = await asyncio.gather(
        *[
            _run_segment_pipeline(
                segment=segment,
                all_segments=segments,
                index=index,
                student_id=student_id,
                conversation_id=conversation_id,
            )
            for index, segment in enumerate(segments)
        ]
    )
    synthesized = synthesize_formatter_node(
        {
            "segment_results": segment_results,
            "node_trace": initial_trace + ["parallel_segment_execution"],
        }
    )
    return {
        "user_text": user_text,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "segments": segments,
        "current_segment_index": len(segments),
        "segment_results": segment_results,
        "final_response": synthesized.get("final_response"),
        "synthesized_response": synthesized.get("synthesized_response"),
        "node_trace": initial_trace + ["parallel_segment_execution"],
    }


async def run_graph(user_text: str, student_id: Optional[int] = None, conversation_id: Optional[int] = None) -> AgentState:
    splitter_state: AgentState = {
        "user_text": user_text,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "current_segment_index": 0,
        "segment_results": [],
        "node_trace": [],
    }
    split_result = await query_splitter_node(splitter_state)
    segments = split_result.get("segments", [user_text]) or [user_text]

    if len(segments) > 1:
        return await _run_parallel_graph_segments(
            user_text=user_text,
            segments=segments,
            student_id=student_id,
            conversation_id=conversation_id,
            initial_trace=split_result.get("node_trace", []),
        )

    compiled = get_compiled_graph()
    initial_state = {
        "user_text": user_text,
        "student_id": student_id,
        "conversation_id": conversation_id,
        "segments": segments,
        "current_segment_index": 0,
        "segment_results": [],
        "node_trace": split_result.get("node_trace", []),
    }
    try:
        return await asyncio.wait_for(compiled.ainvoke(initial_state), timeout=GLOBAL_TIMEOUT)
    except asyncio.TimeoutError:
        initial_state["error"] = "Timeout"
        return initial_state
