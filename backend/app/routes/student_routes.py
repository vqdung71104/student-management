from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Student, LearnedSubject, SemesterGPA, Course
from app.schemas.student_schemas import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter(prefix="/students", tags=["Students"])

# ✅ Create student
@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.dict(exclude={"learned_subjects", "semester_gpa", "enrolled_courses"}))
    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    # Add enrolled_courses
    if student.enrolled_courses:
        for course_id in student.enrolled_courses:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                db_student.enrolled_courses.append(course)

    # Add learned_subjects
    if student.learned_subjects:
        for subj in student.learned_subjects:
            db_subj = LearnedSubject(**subj.dict(), student_id=db_student.id)
            db.add(db_subj)

    # Add semester_gpa
    if student.semester_gpa:
        for gpa in student.semester_gpa:
            db_gpa = SemesterGPA(**gpa.dict(), student_id=db_student.id)
            db.add(db_gpa)

    db.commit()
    db.refresh(db_student)
    return db_student


# ✅ Get all students
@router.get("/", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


# ✅ Get student by ID
@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# ✅ Update student
@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student_update: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in student_update.dict(exclude_unset=True, exclude={"learned_subjects", "semester_gpa"}).items():
        setattr(student, key, value)

    # Update learned_subjects if provided
    if student_update.learned_subjects is not None:
        db.query(LearnedSubject).filter(LearnedSubject.student_id == student.id).delete()
        for subj in student_update.learned_subjects:
            db_subj = LearnedSubject(**subj.dict(), student_id=student.id)
            db.add(db_subj)

    # Update semester_gpa if provided
    if student_update.semester_gpa is not None:
        db.query(SemesterGPA).filter(SemesterGPA.student_id == student.id).delete()
        for gpa in student_update.semester_gpa:
            db_gpa = SemesterGPA(**gpa.dict(), student_id=student.id)
            db.add(db_gpa)

    db.commit()
    db.refresh(student)
    return student


# ✅ Delete student
@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}
