from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, LearnedSubject, SemesterGPA, Course
from app.schemas.student_schemas import StudentCreate, StudentUpdate, StudentResponse

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

    db_student = Student(**student.dict(), email=email)
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
