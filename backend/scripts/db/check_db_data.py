"""Check database data for testing"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== Students ===")
result = db.execute(text("SELECT id, student_name, email, cpa FROM students LIMIT 5")).fetchall()
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, CPA: {row[3]}")

print("\n=== Subject Registers ===")
result = db.execute(text("SELECT student_id, subject_id FROM subject_registers LIMIT 10")).fetchall()
if len(result) > 0:
    print(f"Found {len(result)} subject registrations:")
    for row in result[:5]:
        print(f"  Student: {row[0]}, Subject: {row[1]}")
else:
    print("No subject registrations found")

print("\n=== Subjects ===")
result = db.execute(text("SELECT id, subject_id, subject_name FROM subjects LIMIT 10")).fetchall()
print(f"Found {len(result)} subjects:")
for row in result[:5]:
    print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")

print("\n=== Classes ===")
result = db.execute(text("SELECT class_id, class_name, subject_id FROM classes LIMIT 10")).fetchall()
print(f"Found {len(result)} classes:")
for row in result[:5]:
    print(f"  ClassID: {row[0]}, Name: {row[1]}, SubjectID: {row[2]}")

db.close()
