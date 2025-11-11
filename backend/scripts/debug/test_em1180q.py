"""Test script to check entity extraction"""
import re

# Test the updated regex
questions = [
    "cho tôi lớp của hoc của học phần EM1180Q",
    "các lớp của môn MI1114",
    "tôi muốn xem các lớp Lý thuyết điều khiển tự động",
    "lớp của học phần IT3080",
]

print("=== Testing Entity Extraction ===\n")

for question in questions:
    print(f"Question: {question}")
    
    # Extract subject_id
    subject_id_match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', question)
    if subject_id_match:
        print(f"  subject_id: {subject_id_match.group(1)}")
    
    # Extract subject_name
    subject_patterns = [
        r'các lớp của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'các lớp của học phần ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'lớp của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'lớp của học phần ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'lớp của hoc của học phần ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'các lớp ([A-Z]{2,4}\d{4}[A-Z]?|[A-ZĐĂÂÊÔƠƯ][a-zđăâêôơư]+(?:\s+[a-zđăâêôơư]+)*(?:\s+\d+)?)(?:\s*$|,|\?|\.)',
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if not re.match(r'^[A-Z]{2,4}\d{4}[A-Z]?$', extracted):
                print(f"  subject_name: {extracted}")
            break
    
    print()

print("\n=== Testing Database ===")
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT c.class_id, c.class_name, c.teacher_name, s.subject_id, s.subject_name FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_id = 'EM1180Q'"
result = db.execute(text(sql)).fetchall()
print(f"Query: {sql}")
print(f"Results: {len(result)} rows")
for row in result:
    print(f"  {row}")

db.close()
