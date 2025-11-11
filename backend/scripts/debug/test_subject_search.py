"""Test subject search"""
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Search for subjects with "lý thuyết mạch"
print("=== Searching for classes with 'lý thuyết mạch' ===")
result = db.execute(text("SELECT c.class_id, c.class_name, s.subject_id, s.subject_name FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_name LIKE :pattern LIMIT 10"), {"pattern": "%lý thuyết mạch%"}).fetchall()
print(f"Found: {len(result)} classes")
for row in result:
    print(f"  {row[0]}: {row[1]} | {row[2]}: {row[3]}")

# Try with capitalized
print("\n=== Searching for classes with 'Lý thuyết mạch' (capitalized) ===")
result = db.execute(text("SELECT c.class_id, c.class_name, s.subject_id, s.subject_name FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_name LIKE :pattern LIMIT 10"), {"pattern": "%Lý thuyết mạch%"}).fetchall()
print(f"Found: {len(result)} classes")
for row in result:
    print(f"  {row[0]}: {row[1]} | {row[2]}: {row[3]}")

# Test entity extraction
print("\n=== Testing Entity Extraction ===")
import re

question = "cho tôi các lớp học của môn lý thuyết mạch"
print(f"Question: {question}")

# Try patterns
subject_patterns = [
    r'các lớp của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
    r'các lớp học của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
    r'lớp của môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
    r'môn ([A-Z]{2,4}\d{4}[A-Z]?|[^,\?\.]+?)(?:\s*$|,|\?|\.)',
]

for i, pattern in enumerate(subject_patterns):
    match = re.search(pattern, question, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        print(f"  Pattern {i+1} matched: '{extracted}'")

# Test the SQL that would be generated
print("\n=== Testing SQL Generation ===")
sql_template = "SELECT c.class_id, c.class_name, c.classroom, c.study_date, c.study_time_start, c.study_time_end, c.teacher_name, s.subject_name FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_name LIKE '%Giải tích%'"
subject_name = "lý thuyết mạch"
sql = re.sub(
    r"s\.subject_name LIKE '%[^']+%'",
    f"s.subject_name LIKE '%{subject_name}%'",
    sql_template
)
print(f"Generated SQL: {sql}")

result = db.execute(text(sql)).fetchall()
print(f"Results: {len(result)} rows")
for row in result[:5]:
    print(f"  {row}")

db.close()
