"""
Chatbot Schemas - Pydantic models cho chatbot API
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class PreferenceSummaryItem(BaseModel):
    key: str = Field(..., description="Mã preference")
    label: str = Field(..., description="Nhãn hiển thị thân thiện")
    value: str = Field(..., description="Giá trị đã ghi nhận")
    status: str = Field(..., description="Trạng thái hiển thị cho UI")


class MissingPreferenceItem(BaseModel):
    key: str = Field(..., description="Mã preference còn thiếu")
    label: str = Field(..., description="Nhãn hiển thị thân thiện")
    hint: str = Field(..., description="Gợi ý trả lời ngắn cho người dùng")


class PreferenceProgress(BaseModel):
    completed: int = Field(0, description="Số nhóm preference đã có")
    total: int = Field(5, description="Tổng số nhóm preference")
    percent: int = Field(0, description="Phần trăm hoàn thành")

    model_config = ConfigDict(extra="allow")


class ClassSuggestionUiMetadata(BaseModel):
    """UI metadata — all fields optional so non-class-suggestion intents don't break."""
    title: Optional[str] = Field(default=None, description="Tiêu đề thân thiện")
    subtitle: Optional[str] = Field(default=None, description="Mô tả ngắn")
    status: Optional[str] = Field(default=None, description="Trạng thái hiện tại")
    message: Optional[str] = Field(default=None, description="Thông điệp bổ sung")

    model_config = ConfigDict(extra="allow")


class ClassSuggestionConversationMetadata(BaseModel):
    """Conversation metadata — all fields optional so non-class-suggestion intents don't break."""
    stage: Optional[str] = Field(default=None, description="Trạng thái hội thoại hiện tại")
    next_step: Optional[str] = Field(default=None, description="Bước tiếp theo")
    progress: Optional[PreferenceProgress] = Field(default=None, description="Tiến độ thu thập preference")
    source_choice: Optional[str] = Field(default=None, description="Nguồn học phần đang dùng")
    subject_ids_seed_count: Optional[int] = Field(default=None, description="Số học phần hạt giống")
    nlq_constraints: Optional[Dict[str, Any]] = Field(default=None, description="Ràng buộc NL đã trích xuất")
    current_question: Optional[Dict[str, Any]] = Field(default=None, description="Câu hỏi hiện tại nếu đang collecting")

    model_config = ConfigDict(extra="allow")


class ClassSuggestionPreferencesMetadata(BaseModel):
    """Preferences metadata — all fields optional so non-class-suggestion intents don't break."""
    captured: List[Dict[str, Any]] = Field(default_factory=list, description="Preference đã ghi nhận")
    missing: List[Dict[str, Any]] = Field(default_factory=list, description="Preference còn thiếu")
    auto_captured_keys: List[str] = Field(default_factory=list, description="Preference bắt tự động từ input")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Snapshot preference dạng dict")

    model_config = ConfigDict(extra="allow")


class ClassSuggestionMetadata(BaseModel):
    """
    Unified metadata for both class-suggestion and subject-suggestion intents.

    All sub-fields are plain Optional[Dict] so the schema accepts:
      - Class-suggestion: {"ui": {...}, "conversation": {...}, "preferences": {...}, "result": {...}}
      - Subject-suggestion: {"total_credits": 18, "warning_level": "warning", ...} (extra fields allowed)
      - Other intents: metadata=None
    Extra fields are always allowed so any intent can attach arbitrary metadata.
    """
    ui: Optional[Dict[str, Any]] = Field(default=None, description="Khối hiển thị thân thiện cho FE")
    conversation: Optional[Dict[str, Any]] = Field(default=None, description="Trạng thái hội thoại")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Tổng hợp preference")
    notes: List[str] = Field(default_factory=list, description="Ghi chú hiển thị nhẹ")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Kết quả tóm tắt sau khi tạo gợi ý")

    model_config = ConfigDict(extra="allow")


class ChatMessage(BaseModel):
    """Schema cho tin nhắn chat từ user"""
    message: str = Field(..., description="Tin nhắn từ người dùng", min_length=1)
    student_id: Optional[int] = Field(None, description="ID sinh viên (optional, dùng cho queries cần authentication)")
    conversation_id: Optional[int] = Field(None, description="ID hội thoại (optional, backend tự tạo nếu không gửi)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Làm sao để đăng ký môn học?",
                "student_id": 1
            }
        }


class ChatResponse(BaseModel):
    """Schema cho response từ chatbot"""
    text: str = Field(..., description="Câu trả lời từ chatbot")
    intent: str = Field(..., description="Intent được phân loại")
    confidence: str = Field(..., description="Độ tin cậy: high, medium, low")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Bạn muốn gợi ý đăng ký học phần phải không?",
                "intent": "registration_guide",
                "confidence": "high"
            }
        }


class LLMProcessingMetadata(BaseModel):
    """Schema cho thông tin xử lý trung gian LLM"""
    user_input: str = Field(..., description="Tin nhắn gốc từ user (sau khi normalize)")
    llm_processed_output: Optional[str] = Field(None, description="Kết quả đã xử lý từ LLM")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu thô trước khi format")
    has_repetition: bool = Field(False, description="Có dấu hiệu lặp trong output không")
    repetition_segments: Optional[List[str]] = Field(None, description="Các đoạn bị lặp")
    processing_time_ms: Optional[float] = Field(None, description="Thời gian xử lý tính bằng ms")
    model_used: Optional[str] = Field(None, description="Model LLM được sử dụng")
    token_count: Optional[int] = Field(None, description="Số tokens đã sử dụng")


class ChatResponseWithData(ChatResponse):
    """Schema cho response từ chatbot kèm data từ database"""
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Dữ liệu từ database")
    metadata: Optional[ClassSuggestionMetadata] = Field(None, description="Metadata thân thiện cho UI của class suggestion")
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug info cho frontend console")
    sql: Optional[str] = Field(None, description="SQL query đã thực thi")
    sql_error: Optional[str] = Field(None, description="Lỗi SQL (nếu có)")
    is_compound: bool = Field(False, description="True nếu câu hỏi là compound query (nhiều intent)")
    parts: Optional[List[Dict[str, Any]]] = Field(None, description="Kết quả từng phần khi is_compound=True")
    conversation_id: Optional[int] = Field(None, description="ID hội thoại đã lưu")
    message_id: Optional[int] = Field(None, description="ID bản ghi assistant message")
    created_at: Optional[datetime] = Field(None, description="Thời gian lưu assistant message")
    llm_processing: Optional[LLMProcessingMetadata] = Field(None, description="Thông tin xử lý trung gian từ LLM")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Đây là điểm của bạn (tìm thấy 5 môn học):",
                "intent": "grade_view",
                "confidence": "high",
                "data": [
                    {
                        "subject_name": "Giải tích 1",
                        "credits": 4,
                        "letter_grade": "A",
                        "semester": "2024.1"
                    }
                ],
                "sql": "SELECT ls.subject_name, ls.credits, ls.letter_grade, ls.semester FROM learned_subjects ls WHERE ls.student_id = 1",
                "sql_error": None,
                "llm_processing": {
                    "user_input": "Điểm các môn học kỳ này",
                    "llm_processed_output": "Điểm các môn học kỳ 2024.1",
                    "raw_data": {"semester": "2024.1"},
                    "has_repetition": False,
                    "processing_time_ms": 123.45,
                    "model_used": "gpt-4o-mini",
                    "token_count": 256
                }
            }
        }


class IntentInfo(BaseModel):
    """Schema cho thông tin một intent"""
    tag: str = Field(..., description="Tag của intent")
    description: str = Field(..., description="Mô tả intent")
    examples: list[str] = Field(..., description="Các ví dụ patterns")


class IntentsResponse(BaseModel):
    """Schema cho danh sách các intent"""
    total: int = Field(..., description="Tổng số intent")
    intents: list[IntentInfo] = Field(..., description="Danh sách các intent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 7,
                "intents": [
                    {
                        "tag": "registration_guide",
                        "description": "Hướng dẫn quy trình đăng ký học phần",
                        "examples": [
                            "hướng dẫn đăng ký học phần",
                            "cách đăng ký môn học",
                            "đăng ký học phần như thế nào"
                        ]
                    }
                ]
            }
        }


class ConversationCreateRequest(BaseModel):
    student_id: int = Field(..., description="ID sinh viên")
    title: Optional[str] = Field(None, description="Tiêu đề hội thoại", max_length=255)


class ConversationUpdateRequest(BaseModel):
    student_id: int = Field(..., description="ID sinh viên")
    title: str = Field(..., description="Tiêu đề mới", min_length=1, max_length=255)


class ChatConversationItem(BaseModel):
    id: int
    student_pk: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChatConversationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    has_more: bool = False
    items: List[ChatConversationItem]
    cache_hit: bool = False


class ChatHistoryMessageItem(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    intent: Optional[str] = None
    confidence: Optional[str] = None
    data_json: Optional[Any] = None
    sql_text: Optional[str] = None
    sql_error: Optional[str] = None
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation: ChatConversationItem
    total: int
    page: int
    page_size: int
    has_more: bool = False
    items: List[ChatHistoryMessageItem]
    cache_hit: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Streaming Schema
# ─────────────────────────────────────────────────────────────────────────────

class StreamChunk(BaseModel):
    """Schema cho streaming response chunks"""
    type: str = Field(..., description="Loại chunk: status|data|error|done|metadata", pattern="^(status|data|error|done|metadata)$")
    stage: Optional[str] = Field(None, description="Giai đoạn xử lý: preprocessing|classification|query|formatting|complete|llm_processing")
    message: Optional[str] = Field(None, description="Thông báo cho user")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Thời điểm gửi chunk")
    partial_data: Optional[List[Dict[str, Any]]] = Field(None, description="Dữ liệu một phần (khi type=data)")
    data_count: Optional[int] = Field(None, description="Số lượng bản ghi hiện tại")
    total_count: Optional[int] = Field(None, description="Tổng số bản ghi dự kiến")
    
    # Full response (khi type=done)
    text: Optional[str] = Field(None, description="Câu trả lời hoàn chỉnh")
    intent: Optional[str] = Field(None, description="Intent được phân loại")
    confidence: Optional[str] = Field(None, description="Độ tin cậy")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Dữ liệu hoàn chỉnh")
    metadata: Optional[ClassSuggestionMetadata] = Field(None, description="Metadata cho UI")
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug info cho frontend console")
    is_compound: Optional[bool] = Field(None, description="Có phải compound query")
    parts: Optional[List[Dict[str, Any]]] = Field(None, description="Kết quả từng phần")
    conversation_id: Optional[int] = Field(None, description="ID hội thoại")
    message_id: Optional[int] = Field(None, description="ID assistant message")
    
    # LLM processing metadata (khi type=metadata hoặc type=done)
    llm_processing: Optional[LLMProcessingMetadata] = Field(None, description="Thông tin xử lý trung gian từ LLM")
    
    # Error info (khi type=error)
    error_code: Optional[str] = Field(None, description="Mã lỗi")
    error_detail: Optional[str] = Field(None, description="Chi tiết lỗi")
    
    class Config:
        json_schema_extra = {
            "examples": {
                "status": {
                    "type": "status",
                    "stage": "preprocessing",
                    "message": "✓ Chuẩn hóa dữ liệu",
                    "timestamp": "2025-04-06T10:30:00Z"
                },
                "metadata": {
                    "type": "metadata",
                    "stage": "llm_processing",
                    "message": "Đã hoàn tất xử lý LLM",
                    "llm_processing": {
                        "user_input": "Điểm các môn học kỳ này",
                        "llm_processed_output": "Điểm các môn học kỳ 2024.1",
                        "raw_data": {"semester": "2024.1"},
                        "has_repetition": False,
                        "processing_time_ms": 123.45,
                        "model_used": "gpt-4o-mini",
                        "token_count": 256
                    },
                    "timestamp": "2025-04-06T10:30:03Z"
                },
                "data": {
                    "type": "data",
                    "stage": "query",
                    "message": "Đã lấy 5/120 môn",
                    "partial_data": [{"subject_name": "Giải tích 1"}],
                    "data_count": 5,
                    "total_count": 120,
                    "timestamp": "2025-04-06T10:30:02Z"
                },
                "done": {
                    "type": "done",
                    "stage": "complete",
                    "text": "✅ Tìm thấy 120 môn",
                    "intent": "learned_subjects_view",
                    "confidence": "high",
                    "data": [{"subject_name": "Giải tích 1"}],
                    "llm_processing": {
                        "user_input": "Điểm các môn học kỳ này",
                        "llm_processed_output": "Điểm các môn học kỳ 2024.1",
                        "raw_data": {"semester": "2024.1"},
                        "has_repetition": False
                    },
                    "timestamp": "2025-04-06T10:30:04Z"
                }
            }
        }
