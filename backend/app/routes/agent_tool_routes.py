import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.chatbot_service import ChatbotService
from app.services.text_preprocessor import get_text_preprocessor


router = APIRouter(prefix="/agent-tools", tags=["AgentTools"])

text_preprocessor = get_text_preprocessor()

ALLOWED_TOOL_INTENTS = {
    "grade_view",
    "learned_subjects_view",
    "student_info",
    "subject_info",
    "class_info",
    "schedule_view",
    "subject_registration_suggestion",
    "class_registration_suggestion",
    "modify_schedule",
}


class AgentToolRequest(BaseModel):
    q: str = Field(..., min_length=1)
    student_id: Optional[int] = None
    conversation_id: Optional[int] = None


@router.post("/intent/{intent_name}")
async def execute_intent_tool(
    intent_name: str,
    payload: AgentToolRequest,
    db: Session = Depends(get_db),
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
) -> Dict[str, Any]:
    expected_key = os.environ.get("AGENT_INTERNAL_TOOL_KEY", "dev-agent-key")
    if not x_agent_internal_key or x_agent_internal_key != expected_key:
        print(f"[AGENT-TOOL] forbidden intent={intent_name} has_key={bool(x_agent_internal_key)}")
        raise HTTPException(status_code=403, detail="Forbidden")

    if intent_name not in ALLOWED_TOOL_INTENTS:
        print(f"[AGENT-TOOL] unsupported_intent intent={intent_name}")
        raise HTTPException(status_code=404, detail=f"Unsupported intent tool: {intent_name}")

    from app.routes.chatbot_routes import _process_single_query

    chatbot_service = ChatbotService(db)
    normalized_text = text_preprocessor.preprocess(payload.q)
    preview = normalized_text if len(normalized_text) <= 120 else normalized_text[:120] + "..."
    print(
        f"[AGENT-TOOL] start intent={intent_name} student_id={payload.student_id} "
        f"conversation_id={payload.conversation_id} q={preview}"
    )
    result = await _process_single_query(
        normalized_text=normalized_text,
        student_id=payload.student_id,
        conversation_id=payload.conversation_id,
        db=db,
        chatbot_service=chatbot_service,
        forced_intent=intent_name,
    )
    data_count = len(result.data) if isinstance(result.data, list) else (1 if result.data else 0)
    print(
        f"[AGENT-TOOL] done intent={intent_name} confidence={result.confidence} "
        f"data_count={data_count} sql_error={bool(result.sql_error)}"
    )

    return {
        "text": result.text,
        "intent": result.intent,
        "confidence": result.confidence,
        "data": result.data,
        "metadata": result.metadata.model_dump() if result.metadata else None,
        "sql": result.sql,
        "sql_error": result.sql_error,
    }
