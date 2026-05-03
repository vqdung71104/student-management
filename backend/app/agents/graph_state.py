"""
graph_state.py — TypedDict State for the LangGraph chatbot pipeline.

Giữ tất cả context giữa các Node: câu hỏi gốc, segments đã tách,
intent, constraints (JSON ràng buộc), raw_data, final_response, metadata.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from typing_extensions import NotRequired, TypedDict


# ──────────────────────────────────────────────────────────────────────────────
# Knowledge: Khung giờ học tại Bách Khoa
# Tiết 1–5  = Sáng  (bắt đầu 6:45)
# Tiết 6–12 = Chiều (bắt đầu 12:30)
# Tiết 13+  = Tối
# ──────────────────────────────────────────────────────────────────────────────
PERIOD_TIME_KNOWLEDGE = (
    "Khung giờ học tại ĐH Bách Khoa Hà Nội:\n"
    "  Tiết 1  = 06:45–07:30  |  Tiết 2  = 07:30–08:15\n"
    "  Tiết 3  = 08:15–09:00  |  Tiết 4  = 09:00–09:45\n"
    "  Tiết 5  = 09:45–10:30  |  Tiết 6  = 10:30–11:15\n"
    "  Tiết 7  = 11:15–12:00  |  Tiết 8  = 12:30–13:15\n"
    "  Tiết 9  = 13:15–14:00  |  Tiết 10 = 14:00–14:45\n"
    "  Tiết 11 = 14:45–15:30  |  Tiết 12 = 15:30–16:15\n"
    "  Sáng  = tiết 1–5  (6:45–10:30)\n"
    "  Chiều  = tiết 6–12 (10:30–16:15)\n"
    "  Tối    = tiết 13+  (sau 16:15)\n"
    "Khi người dùng nói 'không học sáng', loại bỏ tất cả các tiết 1–5.\n"
    "Khi người dùng nói 'không học lớp bắt đầu lúc 6:45', loại bỏ tiết 1.\n"
    "Khi người dùng nói 'tránh môn IT1111', loại bỏ mọi class có mã IT1111.\n"
)


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────────
    user_text: str                   # Câu hỏi gốc của sinh viên
    student_id: NotRequired[Optional[int]]
    conversation_id: NotRequired[Optional[int]]

    # ── Intermediate (filled by nodes) ──────────────────────────────────────────
    segments: NotRequired[List[str]]               # Các segment sau query_splitter
    current_segment_index: NotRequired[int]        # Index của segment đang xử lý

    # Intent routing
    intent: NotRequired[Optional[str]]             # intent đã phân loại
    confidence: NotRequired[float]                # confidence score [0..1]
    intent_source: NotRequired[Optional[Literal["tfidf", "llm", "fallback"]]]

    # Route decision
    is_complex: NotRequired[bool]                 # True nếu chứa từ khóa ràng buộc
    needs_agent: NotRequired[bool]               # True → agent branch, False → rule-based

    # Constraint parsing (for complex queries)
    constraints: NotRequired[Optional[Dict[str, Any]]]  # JSON ràng buộc ngữ nghĩa

    # Constraint stripping (intent_router_node strips constraints before TF-IDF)
    clean_query: NotRequired[Optional[str]]   # query sau khi cắt bỏ constraint phrases

    # Tool execution
    raw_data: NotRequired[Optional[Any]]           # Kết quả thô từ Tool

    # Agent filtering (after constraint_parser + tool_executor)
    filtered_data: NotRequired[Optional[Any]]      # Kết quả đã lọc theo constraints

    # Segment results (aggregated)
    segment_results: NotRequired[List[Dict[str, Any]]]
    #   Each item: {
    #     "segment": str,
    #     "intent": Dict,
    #     "raw_result": Any,
    #     "node3_subtype": Optional[str],
    #     "route": Literal["rule_based", "agent", "fallback"],
    #   }

    # ── Output (filled by formatter or fallback) ────────────────────────────────
    final_response: NotRequired[Optional[str]]      # Câu trả lời cuối cùng
    formatted_result: NotRequired[Optional[Dict[str, Any]]]

    # ── Error / fallback tracking ───────────────────────────────────────────────
    error: NotRequired[Optional[str]]
    fallback_reason: NotRequired[Optional[str]]     # "timeout" | "llm_error" | "parse_error" | None
    used_fallback: NotRequired[bool]               # True nếu đã dùng rule-based fallback

    # ── Metadata (passthrough) ─────────────────────────────────────────────────
    node_trace: NotRequired[List[str]]              # Log tên các node đã đi qua
    metadata: NotRequired[Dict[str, Any]]          # Thông tin bổ sung
