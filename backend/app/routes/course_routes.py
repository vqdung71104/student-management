from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Course, CourseSubject
from app.schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

# ✅ Create course
@router.post("/", response_model=CourseResponse)
def create_course(course_data: CourseCreate, db: Session = Depends(get_db)):
    db_course = Course(**course_data.dict(exclude={"subjects"}))
    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    # Add course subjects
    if course_data.subjects:
        for subject_data in course_data.subjects:
            db_course_subject = CourseSubject(
                course_id=db_course.id,
                **subject_data.dict()
            )
            db.add(db_course_subject)

    db.commit()
    db.refresh(db_course)
    return db_course

# ✅ Get all courses
@router.get("/", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

# ✅ Get course by ID
@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# ✅ Update course
@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: str, course_update: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for key, value in course_update.dict(exclude_unset=True, exclude={"subjects"}).items():
        setattr(course, key, value)

    # Update course subjects if provided
    if course_update.subjects is not None:
        db.query(CourseSubject).filter(CourseSubject.course_id == course.id).delete()
        for subject_data in course_update.subjects:
            db_course_subject = CourseSubject(
                course_id=course.id,
                **subject_data.dict()
            )
            db.add(db_course_subject)

    db.commit()
    db.refresh(course)
    return course

# ✅ Delete course
@router.delete("/{course_id}")
def delete_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}
