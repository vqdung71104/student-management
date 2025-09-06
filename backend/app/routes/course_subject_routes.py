from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.__init__ import CourseSubject
from app.schemas.course_subject_schema import CourseSubjectCreate, CourseSubjectUpdate, CourseSubjectResponse

router = APIRouter(prefix="/course-subjects", tags=["Course Subjects"])

# ✅ Create course subject
@router.post("/", response_model=CourseSubjectResponse)
def create_course_subject(course_subject_data: CourseSubjectCreate, db: Session = Depends(get_db)):
    db_course_subject = CourseSubject(**course_subject_data.dict())
    db.add(db_course_subject)
    db.commit()
    db.refresh(db_course_subject)
    
    # Load relationships for response
    course_subject = db.query(CourseSubject).options(
        joinedload(CourseSubject.subject),
        joinedload(CourseSubject.course)
    ).filter(CourseSubject.id == db_course_subject.id).first()
    
    return course_subject

# ✅ Get all course subjects
@router.get("/", response_model=list[CourseSubjectResponse])
def get_course_subjects(db: Session = Depends(get_db)):
    return db.query(CourseSubject).options(
        joinedload(CourseSubject.subject),
        joinedload(CourseSubject.course)
    ).all()

# ✅ Get course subject by ID
@router.get("/{course_subject_id}", response_model=CourseSubjectResponse)
def get_course_subject(course_subject_id: int, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).options(
        joinedload(CourseSubject.subject),
        joinedload(CourseSubject.course)
    ).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")
    return course_subject

# ✅ Update course subject
@router.put("/{course_subject_id}", response_model=CourseSubjectResponse)
def update_course_subject(course_subject_id: int, course_subject_update: CourseSubjectUpdate, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")

    for key, value in course_subject_update.dict(exclude_unset=True).items():
        setattr(course_subject, key, value)

    db.commit()
    
    # Load relationships for response
    updated_course_subject = db.query(CourseSubject).options(
        joinedload(CourseSubject.subject),
        joinedload(CourseSubject.course)
    ).filter(CourseSubject.id == course_subject_id).first()
    
    return updated_course_subject
    db.refresh(course_subject)
    return course_subject

# ✅ Delete course subject
@router.delete("/{course_subject_id}")
def delete_course_subject(course_subject_id: int, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")
    db.delete(course_subject)
    db.commit()
    return {"message": "Course subject deleted successfully"}
