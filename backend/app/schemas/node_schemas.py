"""
Pydantic schemas for NODE endpoints (Agent Tools API).
Contract version: 1.0.0
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    data: Optional[Dict[str, Any]] = None  # None when intent returns only text (e.g. preference question)
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = ConfigDict(extra="allow")  # allows preformatted_text, tool_extra, etc.


# ─────────────────────────────────────────────────────────────────────────────
# NODE-4: Response Formatter
# ─────────────────────────────────────────────────────────────────────────────
class Node4FormatResponseRequest(BaseModel):
    results: Any = Field(..., description="Raw results from tool execution")
    instruction: str = Field(default="Tóm tắt kết quả bằng tiếng Việt", description="Formatting instruction")
    token_budget: Optional[int] = Field(default=160, ge=32, le=512, description="Max tokens for response")
    intent_hints: Optional[List[str]] = Field(
        default=None,
        description="List of intent names (e.g. ['class_registration_suggestion']) "
                    "so Node-4 knows context: preference question vs SQL result",
    )


class Node4FormatResponseResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]  # contains: text (str), tokens_used (int)
    metadata: Dict[str, Any]
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Graduation Progress Tool
# POST /api/agent-tools/intent/graduation_progress
# ─────────────────────────────────────────────────────────────────────────────
class GraduationSubjectItem(BaseModel):
    subject_id: str
    subject_name: str
    credits: int
    learning_semester: Optional[int] = None
    conditional_subjects: Optional[str] = None
    grade: Optional[str] = None  # null = chưa học, "F" = học rồi nhưng chưa đạt
    status: str = Field(
        ...,
        description="'not_taken' = chưa học, 'failed' = học rồi nhưng chưa đạt (grade=F), 'passed' = đã đạt",
    )


class GraduationProgressToolResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str = "success"
    student_id: int
    course_id: int
    course_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured payload used by Node-4 and clients; mirrors the graduation summary.",
    )
    total_required_credits: int = Field(..., description="Tổng tín chỉ yêu cầu của chương trình")
    accumulated_credits: int = Field(..., description="Tổng tín chỉ đã tích lũy (grade đạt)")
    remaining_credits: int = Field(..., description="Tín chỉ còn thiếu = total_required - accumulated")
    passed_subjects: List[GraduationSubjectItem] = Field(default_factory=list)
    missing_subjects: List[GraduationSubjectItem] = Field(
        default_factory=list,
        description="Môn chưa học HOẶC học rồi nhưng chưa đạt (grade=F). "
                    "Mỗi món được gắn status để biết rõ trạng thái.",
    )
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────
class NodeHealthResponse(BaseModel):
    status: str
    version: str = CONTRACT_VERSION
    nodes: Dict[str, bool]
