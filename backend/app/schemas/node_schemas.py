"""
Pydantic schemas for NODE endpoints (Agent Tools API).
Contract version: 1.0.0
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


CONTRACT_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Shared contract envelope
# ─────────────────────────────────────────────────────────────────────────────

class NodeEnvelope(BaseModel):
    status: str = "success"
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NODE-0: Text Preprocessor
# ─────────────────────────────────────────────────────────────────────────────
class Node0PreprocessRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to preprocess")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata to pass through")


class Node0PreprocessResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NODE-1: Query Splitter
# ─────────────────────────────────────────────────────────────────────────────
class Node1QuerySplitterRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to split into queries")
    max_queries: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum number of queries to split into")


class Node1QuerySplitterResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]  # contains: queries[], count, intents[], intent_scores[]
    metadata: Dict[str, Any]
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NODE-2: Intent Classifier
# ─────────────────────────────────────────────────────────────────────────────
class Node2IntentClassifierRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Query to classify intent")


class Node2IntentClassifierResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]  # contains: intent, confidence, confidence_score, etc.
    metadata: Dict[str, Any]
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NODE-3: Tool Executor
# POST /api/agent-tools/intent/{intent_name}
# Intent is in URL path.
# Body accepts both `query` (preferred) and `q` (backward compatible alias).
# Priority rule: if both are provided, `query` takes precedence.
# Validation: at least one of `query` or `q` must be non-null.
# ─────────────────────────────────────────────────────────────────────────────
class Node3ToolExecutorRequest(BaseModel):
    query: Optional[str] = Field(default=None, min_length=1, max_length=5000, description="User query (preferred)")
    q: Optional[str] = Field(default=None, min_length=1, max_length=5000, description="User query (backward compatible alias)")
    student_id: Optional[int] = Field(default=None, description="Student ID")
    conversation_id: Optional[int] = Field(default=None, description="Conversation ID")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")

    @model_validator(mode="after")
    def require_at_least_one_query(self) -> "Node3ToolExecutorRequest":
        if self.query is None and self.q is None:
            raise ValueError("At least one of 'query' or 'q' must be provided")
        return self

    def get_query(self) -> str:
        """Return the query text. `query` takes priority over `q`."""
        return self.query if self.query is not None else (self.q or "")


class Node3ToolExecutorResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]  # contains: text, intent, confidence, data, sql, sql_error
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NODE-4: Response Formatter
# ─────────────────────────────────────────────────────────────────────────────
class Node4FormatResponseRequest(BaseModel):
    results: Any = Field(..., description="Raw results from tool execution")
    instruction: str = Field(default="Tóm tắt kết quả bằng tiếng Việt", description="Formatting instruction")
    token_budget: Optional[int] = Field(default=160, ge=32, le=512, description="Max tokens for response")


class Node4FormatResponseResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]  # contains: text (str), tokens_used (int)
    metadata: Dict[str, Any]
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────
class NodeHealthResponse(BaseModel):
    status: str
    version: str = CONTRACT_VERSION
    nodes: Dict[str, bool]
