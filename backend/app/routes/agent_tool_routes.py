"""
Agent Tools Routes - NODE endpoints for remote LLM agent orchestration.

Contract version: 1.0.0

Exposes internal NODE-0 to NODE-4 as REST endpoints:
- NODE-0: Text Preprocessor  (POST /api/agent-tools/preprocess)
- NODE-1: Query Splitter     (POST /api/agent-tools/node1/query_splitter)
- NODE-2: Intent Classifier  (POST /api/agent-tools/node2/intent_classifier)
- NODE-3: Tool Executor      (POST /api/agent-tools/intent/{intent_name})
- NODE-4: Response Formatter (POST /api/agent-tools/node4/format_response)
- Contract: GET /api/agent-tools/contract
- Health: GET /api/agent-tools/health

All NODE endpoints require X-Agent-Internal-Key header for authentication.
Contract and Health endpoints are public (no auth).
"""
import os
import time
import traceback
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.node_schemas import (
    CONTRACT_VERSION,
    Node0PreprocessRequest,
    Node0PreprocessResponse,
    Node1QuerySplitterRequest,
    Node1QuerySplitterResponse,
    Node2IntentClassifierRequest,
    Node2IntentClassifierResponse,
    Node3ToolExecutorRequest,
    Node3ToolExecutorResponse,
    Node4FormatResponseRequest,
    Node4FormatResponseResponse,
    NodeHealthResponse,
)
from app.services.chatbot_service import ChatbotService
from app.services.text_preprocessor import get_text_preprocessor
from app.services.query_splitter import get_query_splitter


router = APIRouter(prefix="/agent-tools", tags=["AgentTools"])

# ── Singletons ────────────────────────────────────────────────────────────────
_preprocessor_instance = get_text_preprocessor()
_splitter_instance = get_query_splitter()

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


# ── Auth helper ──────────────────────────────────────────────────────────────
def _verify_internal_key(x_agent_internal_key: Optional[str]) -> None:
    expected = os.environ.get("AGENT_INTERNAL_TOOL_KEY", "dev-agent-key")
    if not x_agent_internal_key or x_agent_internal_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


# ═══════════════════════════════════════════════════════════════════════════════
# Contract Publish Endpoint (PUBLIC - no auth required)
# GET /api/agent-tools/contract
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/contract",
    summary="Agent Tools API Contract",
    description="Returns the API contract for remote LLM agent orchestration. "
                "Requires Authorization header (Bearer token) for authentication.",
)
async def get_contract(
    authorization: Optional[str] = Header(None),
):
    """Protected endpoint. Returns contract as JSON dict."""
    try:
        # Log quy trình xác thực API Key
        print("[AgentTools] /contract: Bắt đầu xác thực API Key...")
        expected_key = str(os.getenv("ORCHESTRATOR_API_KEY", "")).strip()
        print(f"[AgentTools] /contract: expected_key (first 7 chars): '{expected_key[:7]}' (length: {len(expected_key)})")

        if not expected_key:
            print("[AgentTools] /contract: ORCHESTRATOR_API_KEY không được thiết lập trong môi trường!")
            raise HTTPException(status_code=500, detail="Server configuration error: ORCHESTRATOR_API_KEY not set")

        if not authorization or not authorization.startswith("Bearer "):
            print(f"[AgentTools] /contract: Thiếu hoặc sai định dạng Authorization header: {authorization}")
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        parts = authorization.split(" ")
        if len(parts) < 2:
            print(f"[AgentTools] /contract: Authorization header format không hợp lệ: {authorization}")
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        token = str(parts[1]).strip()
        print(f"[AgentTools] /contract: token (first 7 chars): '{token[:7]}' (length: {len(token)})")

        if token != expected_key:
            print(f"[AgentTools] /contract: API Key không khớp!\n  - expected_key: '{expected_key}'\n  - token:        '{token}'")
            raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key. Hãy kiểm tra lại biến môi trường ORCHESTRATOR_API_KEY ở backend và token gửi từ FE/Orchestrator. Cả hai phải giống hệt nhau (không thừa/kém ký tự, không có khoảng trắng thừa).")

        print("[AgentTools] /contract: Xác thực API Key thành công!")
        return {
            "version": CONTRACT_VERSION,
            "auth_header": "X-Agent-Internal-Key",
            "auth_required": True,
            "endpoints": {
                "node0_preprocess": {
                    "path": "POST /api/agent-tools/preprocess",
                    "timeout_s": 1,
                    "description": "Normalize Vietnamese text",
                    "request_body": {"text": "string (required, min_length=1)", "metadata": "dict (optional)"},
                    "response_data": {"original_text": "string", "normalized_text": "string", "was_normalized": "bool"},
                },
                "node1_query_splitter": {
                    "path": "POST /api/agent-tools/node1/query_splitter",
                    "timeout_s": 2,
                    "description": "Split compound queries into sub-queries",
                    "request_body": {"text": "string (required)", "max_queries": "int (optional, default=5)"},
                    "response_data": {"queries": "list", "count": "int", "intents": "list", "intent_scores": "list"},
                },
                "node2_intent_classifier": {
                    "path": "POST /api/agent-tools/node2/intent_classifier",
                    "timeout_s": 2,
                    "description": "Classify user intent using TF-IDF + Word2Vec",
                    "request_body": {"query": "string (required, min_length=1)"},
                    "response_data": {
                        "intent": "string",
                        "confidence": "string (high|medium|low)",
                        "confidence_score": "float",
                    },
                },
                "node3_tool_executor": {
                    "path": "POST /api/agent-tools/intent/{intent_name}",
                    "timeout_s": 6,
                    "description": "Execute tool for specific intent",
                    "path_params": {"intent_name": "string. Allowed: " + ", ".join(sorted(ALLOWED_TOOL_INTENTS))},
                    "request_body": {
                        "query": "string (preferred, min_length=1)",
                        "q": "string (backward compat alias, min_length=1)",
                        "student_id": "int (optional)",
                        "conversation_id": "int (optional)",
                        "params": "dict (optional)",
                    },
                    "field_priority": "query takes precedence over q when both are provided",
                    "validation_rule": "At least one of query or q must be provided (422 otherwise)",
                    "response_data": {
                        "text": "string",
                        "intent": "string",
                        "confidence": "string",
                        "data": "list|dict|null",
                        "sql": "string|null",
                        "sql_error": "string|null",
                    },
                },
                "node4_format_response": {
                    "path": "POST /api/agent-tools/node4/format_response",
                    "timeout_s": 12,
                    "description": "Format raw tool results into natural language using LLM",
                    "request_body": {
                        "results": "any (required) - raw results from NODE-3",
                        "instruction": "string (optional, default='Tóm tắt kết quả bằng tiếng Việt')",
                        "token_budget": "int (optional, default=160, max=512)",
                    },
                    "response_data": {"text": "string (str)", "tokens_used": "int"},
                },
            },
            "node3_field_compatibility": {
                "query": {"preferred": True, "description": "User query text"},
                "q": {"preferred": False, "description": "Backward compatible alias for query"},
                "priority_rule": "query takes precedence over q when both are provided",
                "validation_rule": "At least one of 'query' or 'q' must be provided (422 otherwise)",
            },
            "response_envelope": {
                "success": {"status": "success", "data": "any", "metadata": "dict", "error": None},
                "error": {"status": "error", "data": None, "metadata": "dict", "error": "string"},
                "validation_error": "FastAPI default 422 (no custom override)",
            },
        }
    except HTTPException:
        # Re-raise FastAPI HTTP exceptions to be handled by the framework
        raise
    except Exception as e:
        # Catch any other error, log it, and return a 500 with the error message
        import traceback
        print(f"[AgentTools] /contract: Đã xảy ra lỗi: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check (PUBLIC - no auth required)
# GET /api/agent-tools/health
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/health",
    response_model=NodeHealthResponse,
    summary="Agent Tools Health Check",
    description="Check health status of all NODE endpoints. No authentication required.",
)
async def node_health():
    return NodeHealthResponse(
        status="healthy",
        version=CONTRACT_VERSION,
        nodes={
            "node0_preprocess": True,
            "node1_query_splitter": True,
            "node2_intent_classifier": True,
            "node3_tool_executor": True,
            "node4_format_response": True,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-0: Text Preprocessor
# POST /api/agent-tools/preprocess
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/preprocess",
    response_model=Node0PreprocessResponse,
    summary="NODE-0: Text Preprocessor",
    description="Normalize Vietnamese text (spell correction, typo fix, abbreviation expansion).",
)
async def node0_preprocess(
    payload: Node0PreprocessRequest,
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    started_at = time.perf_counter()
    _verify_internal_key(x_agent_internal_key)

    try:
        normalized_text = _preprocessor_instance.preprocess(payload.text)
        duration_ms = (time.perf_counter() - started_at) * 1000
        return Node0PreprocessResponse(
            status="success",
            data={
                "original_text": payload.text,
                "normalized_text": normalized_text,
                "was_normalized": normalized_text != payload.text,
            },
            metadata={
                "node": "node0_preprocess",
                "duration_ms": round(duration_ms, 2),
                "passed_metadata": payload.metadata,
            },
            error=None,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        return Node0PreprocessResponse(
            status="error",
            data=None,
            metadata={"node": "node0_preprocess", "duration_ms": round(duration_ms, 2)},
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-1: Query Splitter
# POST /api/agent-tools/node1/query_splitter
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/node1/query_splitter",
    response_model=Node1QuerySplitterResponse,
    summary="NODE-1: Query Splitter",
    description="Split compound queries into sub-queries using rule-based detection.",
)
async def node1_query_splitter(
    payload: Node1QuerySplitterRequest,
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    started_at = time.perf_counter()
    _verify_internal_key(x_agent_internal_key)

    try:
        max_queries = payload.max_queries or 5
        sub_queries = _splitter_instance.split(payload.text)

        queries = [sq.text for sq in sub_queries[:max_queries]]
        intents = [sq.detected_intent for sq in sub_queries[:max_queries]]
        scores = [round(sq.intent_score, 3) for sq in sub_queries[:max_queries]]
        duration_ms = (time.perf_counter() - started_at) * 1000

        return Node1QuerySplitterResponse(
            status="success",
            data={
                "queries": queries,
                "count": len(queries),
                "intents": intents,
                "intent_scores": scores,
            },
            metadata={
                "node": "node1_query_splitter",
                "duration_ms": round(duration_ms, 2),
                "source": "rule_based",
                "max_queries_requested": payload.max_queries,
            },
            error=None,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        return Node1QuerySplitterResponse(
            status="error",
            data=None,
            metadata={"node": "node1_query_splitter", "duration_ms": round(duration_ms, 2)},
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-2: Intent Classifier
# POST /api/agent-tools/node2/intent_classifier
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/node2/intent_classifier",
    response_model=Node2IntentClassifierResponse,
    summary="NODE-2: Intent Classifier",
    description="Classify user intent using TF-IDF + Word2Vec hybrid approach.",
)
async def node2_intent_classifier(
    payload: Node2IntentClassifierRequest,
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    started_at = time.perf_counter()
    _verify_internal_key(x_agent_internal_key)

    try:
        from app.chatbot.tfidf_classifier import TfidfIntentClassifier

        classifier = TfidfIntentClassifier()
        result = await classifier.classify_intent(payload.query)
        duration_ms = (time.perf_counter() - started_at) * 1000

        return Node2IntentClassifierResponse(
            status="success",
            data={
                "intent": result.get("intent", "unknown"),
                "confidence": result.get("confidence", "low"),
                "confidence_score": result.get("confidence_score", 0.0),
                "method": result.get("method", "unknown"),
                "tfidf_score": result.get("tfidf_score"),
                "semantic_score": result.get("semantic_score"),
                "keyword_score": result.get("keyword_score"),
                "all_scores": result.get("all_scores", [])[:5],
            },
            metadata={
                "node": "node2_intent_classifier",
                "duration_ms": round(duration_ms, 2),
                "source": "tfidf_word2vec",
                "query_length": len(payload.query.split()),
            },
            error=None,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        return Node2IntentClassifierResponse(
            status="error",
            data=None,
            metadata={"node": "node2_intent_classifier", "duration_ms": round(duration_ms, 2)},
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-3: Tool Executor
# POST /api/agent-tools/intent/{intent_name}
#
# Body contract:
#   - query (string, preferred): User query text
#   - q (string, backward compat): Alias for query
#   - student_id (int, optional): Student ID
#   - conversation_id (int, optional): Conversation ID
#   - params (dict, optional): Additional parameters
#
# Priority rule: query takes precedence over q when both are provided.
# Validation: at least one of query or q must be provided. Returns 422 otherwise.
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/intent/{intent_name}",
    response_model=Node3ToolExecutorResponse,
    summary="NODE-3: Tool Executor",
    description="Execute tool for specific intent and return structured data. "
                "Accepts `query` (preferred) or `q` (backward compatible). "
                "If both are provided, `query` takes precedence. "
                "At least one of `query` or `q` must be provided (422 otherwise).",
)
async def execute_intent_tool(
    intent_name: str,
    payload: Node3ToolExecutorRequest,
    db: Session = Depends(get_db),
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    started_at = time.perf_counter()
    _verify_internal_key(x_agent_internal_key)

    if intent_name not in ALLOWED_TOOL_INTENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported intent tool: {intent_name}. Allowed: {sorted(ALLOWED_TOOL_INTENTS)}",
        )

    try:
        from app.routes.chatbot_routes import _process_single_query

        chatbot_service = ChatbotService(db)
        query_text = payload.get_query()
        normalized_text = _preprocessor_instance.preprocess(query_text)

        preview = normalized_text if len(normalized_text) <= 120 else normalized_text[:120] + "..."
        print(
            f"[AGENT-TOOL][NODE3] start intent={intent_name} student_id={payload.student_id} "
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
        duration_ms = (time.perf_counter() - started_at) * 1000

        print(
            f"[AGENT-TOOL][NODE3] done intent={intent_name} confidence={result.confidence} "
            f"data_count={data_count} duration_ms={duration_ms:.1f}"
        )

        return Node3ToolExecutorResponse(
            status="success",
            data={
                "text": result.text,
                "intent": result.intent,
                "confidence": result.confidence,
                "data": result.data,
                "sql": result.sql,
                "sql_error": result.sql_error,
            },
            metadata={
                "node": "node3_tool_executor",
                "duration_ms": round(duration_ms, 2),
                "intent": intent_name,
                "data_count": data_count,
            },
            error=None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        print(f"[AGENT-TOOL][NODE3] error intent={intent_name} error={exc}")
        return Node3ToolExecutorResponse(
            status="error",
            data=None,
            metadata={"node": "node3_tool_executor", "duration_ms": round(duration_ms, 2), "intent": intent_name},
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE-4: Response Formatter
# POST /api/agent-tools/node4/format_response
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/node4/format_response",
    response_model=Node4FormatResponseResponse,
    summary="NODE-4: Response Formatter",
    description="Format raw tool results into natural language response using LLM.",
)
async def node4_format_response(
    payload: Node4FormatResponseRequest,
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    started_at = time.perf_counter()
    _verify_internal_key(x_agent_internal_key)

    try:
        from app.agents.agent_orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        formatted_text = await orchestrator.node4_response_formatter(
            raw_result=payload.results,
            instruction=payload.instruction,
        )

        estimated_tokens = len(formatted_text) // 2
        duration_ms = (time.perf_counter() - started_at) * 1000

        return Node4FormatResponseResponse(
            status="success",
            data={
                "text": formatted_text,
                "tokens_used": estimated_tokens,
            },
            metadata={
                "node": "node4_format_response",
                "duration_ms": round(duration_ms, 2),
                "instruction": payload.instruction,
                "token_budget": payload.token_budget,
                "source": "llm",
            },
            error=None,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        print(f"[AGENT-TOOL][NODE4] error error={exc}")
        return Node4FormatResponseResponse(
            status="error",
            data=None,
            metadata={"node": "node4_format_response", "duration_ms": round(duration_ms, 2)},
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Introspection
# GET /api/agent-tools/intents
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/intents",
    summary="List Available Intents",
    description="Get list of supported intents for NODE-3 tool execution.",
)
async def list_intents(
    x_agent_internal_key: Optional[str] = Header(None, alias="X-Agent-Internal-Key"),
):
    _verify_internal_key(x_agent_internal_key)
    return {
        "status": "success",
        "intents": sorted(ALLOWED_TOOL_INTENTS),
        "count": len(ALLOWED_TOOL_INTENTS),
    }
