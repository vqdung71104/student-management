"""
graph_state.py — TypedDict State for the LangGraph chatbot pipeline.
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Annotated
import operator
from typing_extensions import NotRequired, TypedDict

PERIOD_TIME_KNOWLEDGE = (
    "Khung giờ học tại ĐH Bách Khoa Hà Nội:\n"
    "  Tiết 1  = 06:45–07:30  |  Tiết 2  = 07:30–08:15\n"
    "  Tiết 3  = 08:15–09:00  |  Tiết 4  = 09:00–09:45\n"
    "  Tiết 5  = 09:45–10:30  |  Tiết 6  = 10:30–11:15\n"
    "  Tiết 7  = 11:15–12:00  |  Tiết 8  = 12:30–13:15\n"
    "  Tiết 9  = 13:15–14:00  |  Tiết 10 = 14:00–14:45\n"
    "  Tiết 11 = 14:45–15:30  |  Tiết 12 = 15:30–16:15\n"
    "  Sáng  = tiết 1–5  (6:45–10:30) | Chiều  = tiết 6–12 (10:30–16:15) | Tối = tiết 13+ (sau 16:15)\n"
    "Khi người dùng nói 'không học sáng', loại bỏ tất cả các tiết 1–5.\n"
    "Khi người dùng nói 'tránh môn IT1111', loại bỏ mọi class có mã IT1111.\n"
)

class AgentState(TypedDict):
    # Input tĩnh (Không ghi đè trong các Node)
    user_text: str                   
    student_id: NotRequired[Optional[int]]
    conversation_id: NotRequired[Optional[int]]

    # Fields bị thay thế (Overwrite) trong quá trình chạy
    segments: NotRequired[List[str]]               
    current_segment_index: NotRequired[int]        
    intent: NotRequired[Optional[str]]             
    confidence: NotRequired[float]                
    intent_source: NotRequired[Optional[str]]
    is_complex: NotRequired[bool]                 
    needs_agent: NotRequired[bool]               
    constraints: NotRequired[Optional[Dict[str, Any]]]  
    clean_query: NotRequired[Optional[str]]   
    raw_data: NotRequired[Optional[Any]]           
    filtered_data: NotRequired[Optional[Any]]      
    needs_agent_filter: NotRequired[bool]
    
    final_response: NotRequired[Optional[str]]      
    formatted_result: NotRequired[Optional[Dict[str, Any]]]
    synthesized_response: NotRequired[Optional[str]]
    error: NotRequired[Optional[str]]
    fallback_reason: NotRequired[Optional[str]]     
    used_fallback: NotRequired[bool]               

    # Fields TÍCH LŨY (Dùng operator.add để append, KHÔNG ĐƯỢC overwrite)
    segment_results: NotRequired[Annotated[List[Dict[str, Any]], operator.add]]
    node_trace: NotRequired[Annotated[List[str], operator.add]]
    metadata: NotRequired[Dict[str, Any]]