"""
Quick test script for entity extraction improvements
Tests patterns like "các lớp môn học [name]" without "của"
"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.services.nl2sql_service import NL2SQLService


def test_entity_extraction():
    """Test entity extraction with various patterns"""
    service = NL2SQLService()
    
    test_cases = [
        # Original patterns (should still work)
        "các lớp của môn Giải tích I",
        "các lớp của học phần Lập trình mạng",
        "lớp của môn MI1114",
        
        # New patterns WITHOUT "của"
        "cho tôi thông tin các lớp môn học Cơ sở dữ liệu",
        "thông tin các lớp môn học Lập trình mạng",
        "các lớp môn Nhập môn học máy và trí tuệ nhân tạo",
        "các lớp học phần Cơ sở dữ liệu",
        "các lớp Thuật toán ứng dụng",
        
        # Edge cases
        "cho tôi các lớp Toán rời rạc",
        "thông tin lớp môn Lập trình mạng",
        "các lớp môn IT3080",
        "các lớp Đại số tuyến tính",
        "các lớp Nguyên lý hệ điều hành",
        
        # With subject ID
        "các lớp môn EM1180Q",
        "các lớp học phần MI1114",
    ]
    
    print("=" * 80)
    print("ENTITY EXTRACTION TEST - Class Info Patterns")
    print("=" * 80)
    
    for i, question in enumerate(test_cases, 1):
        entities = service._extract_entities(question)
        
        print(f"\n[Test {i}]")
        print(f"Question: '{question}'")
        print(f"Entities: {entities}")
        
        # Debug: test regex directly
        import re
        test_pattern = r'(?:các lớp|cho tôi các lớp|thông tin các lớp)\s+([A-ZĐĂÂÊÔƠƯ][a-zđăâêôơư]+(?:\s+[a-zđăâêôơư]+)*(?:\s+\d+)?)(?:\s*$|,|\?|\.)'
        match = re.search(test_pattern, question, re.IGNORECASE)
        if match and not entities:
            print(f"  DEBUG: Pattern matched '{match.group(1)}' but not extracted!")
        
        # Validate
        has_subject_info = 'subject_id' in entities or 'subject_name' in entities
        status = "✓ PASS" if has_subject_info else "✗ FAIL"
        print(f"Status: {status}")
        
        if 'subject_id' in entities:
            print(f"  → Will search by subject_id = '{entities['subject_id']}'")
        elif 'subject_name' in entities:
            print(f"  → Will search by subject_name LIKE '%{entities['subject_name']}%'")
        else:
            print(f"  → ⚠️ No subject extracted! Entity extraction failed.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_entity_extraction()
