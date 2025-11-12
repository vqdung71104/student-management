"""Find Kỹ năng mềm subjects"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

result = db.execute(text("""
    SELECT id, subject_id, subject_name 
    FROM subjects 
    WHERE subject_name LIKE '%Kỹ năng mềm%' 
       OR subject_name LIKE '%Văn hóa%'
    LIMIT 10
""")).fetchall()

print(f'Found {len(result)} subjects:')
for r in result:
    print(f'  ID: {r[0]}, Code: {r[1]}, Name: {r[2]}')

if len(result) > 0:
    print("\n=== Inserting subject_registers for student 1 ===")
    
    for subject in result:
        try:
            db.execute(text("""
                INSERT INTO subject_registers (student_id, subject_id, register_date)
                VALUES (:student_id, :subject_id, NOW())
            """), {"student_id": 1, "subject_id": subject[0]})
            print(f"✓ Registered: {subject[2]}")
        except Exception as e:
            if "Duplicate entry" in str(e):
                print(f"⚠ Already registered: {subject[2]}")
            else:
                print(f"✗ Error for {subject[2]}: {e}")
    
    db.commit()
    
    # Verify
    print("\n=== Verification ===")
    verify = db.execute(text("""
        SELECT sr.student_id, s.subject_id, s.subject_name
        FROM subject_registers sr
        JOIN subjects s ON sr.subject_id = s.id
        WHERE sr.student_id = 1
    """)).fetchall()
    
    print(f"Student 1 has {len(verify)} registered subjects:")
    for row in verify:
        print(f"  - {row[1]}: {row[2]}")
    
    # Check available classes
    print("\n=== Available classes for registered subjects ===")
    classes = db.execute(text("""
        SELECT c.class_id, c.class_name, s.subject_name, s.subject_id
        FROM classes c
        JOIN subjects s ON c.subject_id = s.id
        WHERE s.id IN (SELECT subject_id FROM subject_registers WHERE student_id = 1)
        LIMIT 10
    """)).fetchall()
    
    print(f"Found {len(classes)} classes:")
    for row in classes:
        print(f"  - {row[0]}: {row[1]} | {row[2]} ({row[3]})")
else:
    print("⚠ No matching subjects found")

db.close()
