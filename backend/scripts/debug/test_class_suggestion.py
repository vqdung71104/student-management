"""Test class registration suggestion with new logic"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.db.database import SessionLocal
from sqlalchemy import text
import re

db = SessionLocal()

# Assume student_id = 1 for testing
student_id = 1

print("=== Test 1: Get student's registered subjects ===")
sql1 = "SELECT s.subject_id, s.subject_name FROM subject_registers sr JOIN subjects s ON sr.subject_id = s.id WHERE sr.student_id = :student_id"
result = db.execute(text(sql1), {"student_id": student_id}).fetchall()
print(f"Student {student_id} has registered {len(result)} subjects:")
for row in result[:5]:
    print(f"  - {row[0]}: {row[1]}")

print("\n=== Test 2: Get classes for registered subjects ===")
sql2 = "SELECT c.class_id, c.class_name, c.classroom, c.study_date, c.study_time_start, c.study_time_end, c.teacher_name, s.subject_name, s.subject_id FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.id IN (SELECT subject_id FROM subject_registers WHERE student_id = :student_id) ORDER BY s.subject_name, c.study_date LIMIT 10"
result = db.execute(text(sql2), {"student_id": student_id}).fetchall()
print(f"Found {len(result)} classes for registered subjects:")
for row in result[:5]:
    print(f"  - {row[0]}: {row[1]} | {row[7]} ({row[8]})")

print("\n=== Test 3: Get classes filtered by subject name ===")
subject_name = "Triết học Mác - Lênin"
sql3 = "SELECT c.class_id, c.class_name, c.classroom, c.study_date, s.subject_name, s.subject_id FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.id IN (SELECT subject_id FROM subject_registers WHERE student_id = :student_id) AND s.subject_name LIKE :pattern ORDER BY c.study_date LIMIT 5"
result = db.execute(text(sql3), {"student_id": student_id, "pattern": f"%{subject_name}%"}).fetchall()
print(f"Found {len(result)} classes for '{subject_name}':")
for row in result:
    print(f"  - {row[0]}: {row[1]} | {row[4]} ({row[5]})")

print("\n=== Test 4: Entity Extraction ===")
questions = [
    "kỳ này nên học lớp nào",
    "tôi nên học lớp nào của môn Triết học Mác - Lênin",
    "tôi nên học lớp nào của môn SSH1111",
]

for question in questions:
    print(f"\nQuestion: {question}")
    
    # Extract subject_id
    subject_id_match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', question)
    if subject_id_match:
        print(f"  subject_id: {subject_id_match.group(1)}")
    
    # Extract subject_name
    subject_patterns = [
        r'lớp nào của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
        r'môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if not re.match(r'^[A-Z]{2,4}\d{4}[A-Z]?$', extracted):
                print(f"  subject_name: {extracted}")
            break

db.close()
