"""
Test entity extraction for subject names
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.nl2sql_service import NL2SQLService

# Initialize service
nl2sql = NL2SQLService()

# Test cases
test_questions = [
    "thông tin lớp Kỹ thuật điện",
    "thông tin lớp Điều khiển nội mạng",
    "danh sách lớp môn Lý thuyết điều khiển tự động",
    "các lớp của môn Cảm biến do lường và xử lý tín hiệu đo",
    "thông tin các lớp Kỹ thuật điện",
    "các lớp Giải tích 1",
    "lớp môn IT4040",
]

print("=" * 80)
print("TESTING ENTITY EXTRACTION")
print("=" * 80)

for question in test_questions:
    print(f"\n📝 Question: {question}")
    entities = nl2sql._extract_entities(question)
    print(f"✅ Entities: {entities}")
    
    if 'subject_name' in entities:
        print(f"   ✓ Subject name extracted: '{entities['subject_name']}'")
    elif 'subject_id' in entities:
        print(f"   ✓ Subject ID extracted: '{entities['subject_id']}'")
    else:
        print(f"   ✗ No subject extracted!")

print("\n" + "=" * 80)
