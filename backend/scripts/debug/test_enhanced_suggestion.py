"""Test enhanced class registration suggestion with learned_subjects filtering"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

student_id = 1

print("=== Student Info ===")
student = db.execute(text("""
    SELECT id, student_name, cpa, failed_subjects_number, study_subjects_number
    FROM students WHERE id = :student_id
"""), {"student_id": student_id}).fetchone()

print(f"ID: {student[0]}")
print(f"Name: {student[1]}")
print(f"CPA: {student[2]}")
print(f"Failed subjects: {student[3]}")
print(f"Study subjects: {student[4]}")

print("\n=== Subject Registers (môn đã đăng ký) ===")
subject_registers = db.execute(text("""
    SELECT s.id, s.subject_id, s.subject_name, s.conditional_subjects
    FROM subject_registers sr
    JOIN subjects s ON sr.subject_id = s.id
    WHERE sr.student_id = :student_id
"""), {"student_id": student_id}).fetchall()

print(f"Found {len(subject_registers)} registered subjects:")
for row in subject_registers:
    print(f"  - {row[1]}: {row[2]} (Conditional: {row[3] or 'None'})")

print("\n=== Learned Subjects (môn đã học) ===")
learned_subjects = db.execute(text("""
    SELECT s.subject_id, s.subject_name, ls.letter_grade
    FROM learned_subjects ls
    JOIN subjects s ON ls.subject_id = s.id
    WHERE ls.student_id = :student_id
    ORDER BY s.subject_name
"""), {"student_id": student_id}).fetchall()

print(f"Found {len(learned_subjects)} learned subjects:")
for row in learned_subjects[:10]:
    print(f"  - {row[0]}: {row[1]} (Grade: {row[2]})")

print("\n=== Enhanced Class Registration Suggestion ===")
print("SQL: Classes from subject_registers, excluding already-learned (except F/I)")

enhanced_sql = """
SELECT 
    c.class_id, 
    c.class_name, 
    c.classroom, 
    c.study_date, 
    c.study_time_start, 
    c.study_time_end, 
    c.teacher_name, 
    s.subject_name, 
    s.subject_id,
    s.conditional_subjects
FROM classes c 
JOIN subjects s ON c.subject_id = s.id 
WHERE s.id IN (
    SELECT subject_id 
    FROM subject_registers 
    WHERE student_id = :student_id
) 
AND s.id NOT IN (
    SELECT subject_id 
    FROM learned_subjects 
    WHERE student_id = :student_id 
    AND letter_grade NOT IN ('F', 'I')
)
ORDER BY s.subject_name, c.study_date
LIMIT 10
"""

result = db.execute(text(enhanced_sql), {"student_id": student_id}).fetchall()

print(f"\nFound {len(result)} classes to suggest:")
for row in result:
    print(f"\n  Class ID: {row[0]}")
    print(f"  Name: {row[1]}")
    print(f"  Subject: {row[7]} ({row[8]})")
    print(f"  Schedule: {row[3]} {row[4]}-{row[5]}")
    print(f"  Classroom: {row[2]}")
    print(f"  Teacher: {row[6]}")
    print(f"  Conditional: {row[9] or 'None'}")

print("\n=== Comparison: Old SQL (without learned_subjects filter) ===")
old_sql = """
SELECT c.class_id, s.subject_name, s.subject_id
FROM classes c 
JOIN subjects s ON c.subject_id = s.id 
WHERE s.id IN (
    SELECT subject_id 
    FROM subject_registers 
    WHERE student_id = :student_id
)
ORDER BY s.subject_name
LIMIT 10
"""

old_result = db.execute(text(old_sql), {"student_id": student_id}).fetchall()
print(f"Old query would return {len(old_result)} classes (including already-learned)")

db.close()
