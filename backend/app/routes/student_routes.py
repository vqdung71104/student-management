from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, LearnedSubject, SemesterGPA, Course
from app.schemas.student_schemas import StudentCreate, StudentUpdate, StudentResponse
from app.utils.grade_calculator import letter_grade_to_score
import hashlib

router = APIRouter(prefix="/students", tags=["Students"])


# ✅ Create student
@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    # Check trùng student_id
    if db.query(Student).filter(Student.student_id == student.student_id).first():
        raise HTTPException(status_code=400, detail="student_id đã tồn tại")

    # Auto-generate email
    email = student.generate_email()
    if db.query(Student).filter(Student.email == email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    # Create student with manual fields + auto-calculated defaults
    student_data = student.dict()
    student_data.update({
        'email': email,
        'cpa': 0.0,
        'failed_subjects_number': 0,
        'study_subjects_number': 0,
        'total_failed_credits': 0,
        'total_learned_credits': 0,
        'year_level': "Trình độ năm 1",
        'warning_level': "Cảnh cáo mức 0",
        'level_3_warning_number': 0,
        # Thêm thông tin đăng nhập với mật khẩu mặc định
        'login_password': hashlib.md5("123456".encode()).hexdigest()  # Hash mật khẩu mặc định
    })

    db_student = Student(**student_data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


# ✅ Get all students
@router.get("/", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


# ✅ Get student by id
@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên") #không thấy sinh viên
    return student


# ✅ Update student
@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, student_update: StudentUpdate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    update_data = student_update.dict(exclude_unset=True)

    # Nếu có thay đổi student_name hoặc student_id -> regenerate email
    if "student_name" in update_data or "student_id" in update_data:
        tmp_student = StudentCreate(**{**db_student.__dict__, **update_data})
        update_data["email"] = tmp_student.generate_email()

    for key, value in update_data.items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)
    return db_student


# ✅ Delete student
@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.student_id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    db.delete(db_student)
    db.commit()
    return {"detail": "Xóa sinh viên thành công"}


# ✅ Get student with detailed academic information
@router.get("/{student_id}/academic-details")
def get_student_academic_details(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    
    # Get all semester GPAs using student.id (not student_id)
    semester_gpas = db.query(SemesterGPA).filter(SemesterGPA.student_id == student.id).all()
    
    # Get all learned subjects using student.id (not student_id)
    learned_subjects = db.query(LearnedSubject).filter(LearnedSubject.student_id == student.id).all()
    
    # Calculate overall GPA
    total_credits = sum([ls.credits for ls in learned_subjects])
    total_grade_points = sum([
        ls.credits * letter_grade_to_score(ls.letter_grade) 
        for ls in learned_subjects
    ])
    overall_gpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    
    # Map learned subjects với subject_code từ relationship
    learned_subjects_data = []
    for ls in learned_subjects:
        ls_dict = {
            "id": ls.id,
            "subject_name": ls.subject_name,
            "credits": ls.credits,
            "final_score": ls.final_score,
            "midterm_score": ls.midterm_score,
            "weight": ls.weight,
            "total_score": ls.total_score,
            "letter_grade": ls.letter_grade,
            "semester": ls.semester,
            "student_id": ls.student_id,
            "subject_id": ls.subject_id,
            "subject_code": ls.subject.subject_id if ls.subject else None  # Mã HP từ Subject
        }
        learned_subjects_data.append(ls_dict)
    
    return {
        "student": student,
        "semester_gpas": semester_gpas,
        "learned_subjects": learned_subjects_data,
        "overall_gpa": round(overall_gpa, 2),
        "total_credits": total_credits,
        "total_learned_credits": student.total_learned_credits,
        "total_failed_credits": student.total_failed_credits,
        "warning_level": student.warning_level,
        "year_level": student.year_level
    }
