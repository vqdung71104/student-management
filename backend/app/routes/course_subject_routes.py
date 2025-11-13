from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.__init__ import Course, CourseSubject, Subject
from app.schemas.course_subject_schema import CourseSubjectCreate, CourseSubjectUpdate, CourseSubjectResponse

router = APIRouter(prefix="/course-subjects", tags=["Course Subjects"])

#    Create course + course_subjects từ request phức tạp
@router.post("/", response_model=list[CourseSubjectResponse])
def create_course_with_subjects(request_data: dict, db: Session = Depends(get_db)):
    # 1. Tạo course mới
    course_id_str = request_data.get("course_id")
    course_name = request_data.get("course_name")
    subjects = request_data.get("subjects", [])

    if not course_id_str or not course_name:
        raise HTTPException(status_code=400, detail="course_id and course_name are required")

    # kiểm tra trùng course_id
    existing_course = db.query(Course).filter(Course.course_id == course_id_str).first()
    if existing_course:
        raise HTTPException(status_code=400, detail="Course ID already exists")

    db_course = Course(course_id=course_id_str, course_name=course_name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    # 2. Với mỗi subject, tìm subject.id rồi tạo course_subject
    created_course_subjects = []
    for subj in subjects:
        subj_id_str = subj.get("subject_id")
        learning_semester = subj.get("learning_semester", 1)  # Default semester 1
        subject = db.query(Subject).filter(Subject.subject_id == subj_id_str).first()
        if not subject:
            raise HTTPException(status_code=404, detail=f"Subject with subject_id '{subj_id_str}' not found")

        db_course_subject = CourseSubject(
            course_id=db_course.id,   # int PK
            subject_id=subject.id,    # int PK
            learning_semester=learning_semester  # Thêm learning_semester
        )
        db.add(db_course_subject)
        db.commit()
        db.refresh(db_course_subject)

        created_course_subjects.append(db_course_subject)

    return created_course_subjects


#    Get all course subjects
@router.get("/", response_model=list[CourseSubjectResponse])
def get_course_subjects(db: Session = Depends(get_db)):
    return db.query(CourseSubject).all()


#    Get course subject by ID
@router.get("/{course_subject_id}", response_model=CourseSubjectResponse)
def get_course_subject(course_subject_id: int, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")
    return course_subject


#    Update course subject
@router.put("/{course_subject_id}", response_model=CourseSubjectResponse)
def update_course_subject(course_subject_id: int, course_subject_update: CourseSubjectUpdate, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")

    for key, value in course_subject_update.dict(exclude_unset=True).items():
        setattr(course_subject, key, value)

    db.commit()
    db.refresh(course_subject)
    return course_subject


#    Delete course subject
@router.delete("/{course_subject_id}")
def delete_course_subject(course_subject_id: int, db: Session = Depends(get_db)):
    course_subject = db.query(CourseSubject).filter(CourseSubject.id == course_subject_id).first()
    if not course_subject:
        raise HTTPException(status_code=404, detail="Course subject not found")
    db.delete(course_subject)
    db.commit()
    return {"message": "Course subject deleted successfully"}
