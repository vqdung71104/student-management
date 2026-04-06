"""
Test streaming syntax và logic tách biệt - không cần học viên chi tiết
"""
import sys
import json
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Kiểm tra StreamChunk schema
class StreamChunk(BaseModel):
    """Schema cho streaming response chunks"""
    type: str = Field(..., description="Loại chunk: status|data|error|done")
    stage: Optional[str] = Field(None, description="Giai đoạn xử lý")
    message: Optional[str] = Field(None, description="Thông báo cho user")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    partial_data: Optional[List[Dict[str, Any]]] = Field(None)
    data_count: Optional[int] = Field(None)
    total_count: Optional[int] = Field(None)
    data: Optional[List[Dict[str, Any]]] = Field(None)
    text: Optional[str] = Field(None)
    intent: Optional[str] = Field(None)
    confidence: Optional[str] = Field(None)
    error_code: Optional[str] = Field(None)
    error_detail: Optional[str] = Field(None)


# Test 1: Kiểm tra StreamChunk serialization
def test_stream_chunk_serialization():
    """Test StreamChunk có thể convert qua JSON"""
    chunk = StreamChunk(
        type="status",
        stage="preprocessing",
        message="✓ Chuẩn hóa dữ liệu hoàn tất",
    )
    
    # Use mode='json' để Pydantic convert datetime
    chunk_dict = chunk.model_dump(exclude_none=True, mode='json')
    json_str = json.dumps(chunk_dict, ensure_ascii=False)
    
    assert "status" in json_str
    assert "preprocessing" in json_str
    print(f"✅ Test 1 passed: StreamChunk serialization")
    print(f"   JSON: {json_str}")


# Test 2: Test streaming generator syntax
async def mock_streaming_generator() -> AsyncGenerator[StreamChunk, None]:
    """Mock streaming generator - kiểm tra async/await syntax"""
    
    # Phase 1
    yield StreamChunk(
        type="status",
        stage="preprocessing",
        message="✓ Chuẩn hóa dữ liệu hoàn tất",
    )
    
    # Phase 2
    yield StreamChunk(
        type="status",
        stage="classification",
        message="✓ Phân loại: learned_subjects_view (high)",
    )
    
    # Phase 3
    yield StreamChunk(
        type="status",
        stage="query",
        message="🔄 Đang truy vấn cơ sở dữ liệu...",
    )
    
    # Phase 4: Data partial
    partial_data = [
        {"subject_name": "Giải tích 1", "credits": 4},
        {"subject_name": "Đại số tuyến tính", "credits": 4},
    ]
    yield StreamChunk(
        type="data",
        stage="query",
        message="✓ Lấy được 2 kết quả",
        partial_data=partial_data,
        data_count=2,
        total_count=120,
    )
    
    # Phase 5: Done
    full_data = partial_data + [
        {"subject_name": "Hóa học", "credits": 3},
    ]
    yield StreamChunk(
        type="done",
        stage="complete",
        text="✅ Tìm thấy 120 môn",
        intent="learned_subjects_view",
        confidence="high",
        data=full_data,
    )


async def test_streaming_generator():
    """Test generator async"""
    chunks = []
    async for chunk in mock_streaming_generator():
        chunks.append(chunk)
        chunk_dict = chunk.model_dump(exclude_none=True, mode='json')
        json_str = json.dumps(chunk_dict, ensure_ascii=False)
        print(f"  Chunk {len(chunks)}: {chunk.type} - {chunk.stage} - {json_str[:60]}...")
    
    assert len(chunks) == 5, f"Expected 5 chunks, got {len(chunks)}"
    assert chunks[0].type == "status"
    assert chunks[-1].type == "done"
    assert chunks[-1].data is not None
    print(f"✅ Test 2 passed: Streaming generator syntax ({len(chunks)} chunks)")


# Test 3: Test SSE event format
def test_sse_format():
    """Test SSE event format"""
    chunk = StreamChunk(
        type="data",
        stage="query",
        message="✓ Lấy được 10 kết quả",
        data_count=10,
    )
    chunk_dict = chunk.model_dump(exclude_none=True, mode='json')
    json_str = json.dumps(chunk_dict, ensure_ascii=False)
    sse_event = f"data: {json_str}\n\n"
    
    assert sse_event.startswith("data: ")
    assert sse_event.endswith("\n\n")
    print(f"✅ Test 3 passed: SSE format")
    print(f"   Event: {sse_event[:80]}...")


# Test 4: Test error handling
def test_error_chunk():
    """Test error chunk"""
    error_chunk = StreamChunk(
        type="error",
        message="Có lỗi xảy ra khi xử lý câu hỏi",
        error_code="processing_error",
        error_detail="Database connection failed",
    )
    
    error_dict = error_chunk.model_dump(exclude_none=True, mode='json')
    assert error_dict["type"] == "error"
    assert "error_code" in error_dict
    print(f"✅ Test 4 passed: Error chunk format")


# Test 5: Test data chunking
def test_data_chunking():
    """Test chunking lớn data thành các phần"""
    large_data = [
        {"id": i, "name": f"subject_{i}", "credits": 3}
        for i in range(1, 101)
    ]
    
    # Simulate chunking
    chunk_size = 10
    for i in range(0, len(large_data), chunk_size):
        chunk = large_data[i:i+chunk_size]
        stream_chunk = StreamChunk(
            type="data",
            stage="query",
            message=f"Đã lấy {i + len(chunk)}/{len(large_data)} bản ghi",
            partial_data=chunk,
            data_count=i + len(chunk),
            total_count=len(large_data),
        )
        
        chunk_dict = stream_chunk.model_dump(exclude_none=True, mode='json')
        assert len(chunk_dict["partial_data"]) <= chunk_size
    
    print(f"✅ Test 5 passed: Data chunking ({len(large_data)} items in {chunk_size} chunks)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING STREAMING TESTS")
    print("="*60 + "\n")
    
    try:
        # Synchronous tests
        test_stream_chunk_serialization()
        test_sse_format()
        test_error_chunk()
        test_data_chunking()
        
        # Async test
        import asyncio
        asyncio.run(test_streaming_generator())
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
