from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Course, CourseSubject, Subject
from app.schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


# ✅ Create course
@router.post("/", response_model=CourseResponse)
def create_course(course_data: CourseCreate, db: Session = Depends(get_db)):
    # Kiểm tra xem course_id đã tồn tại chưa
    existing_course = db.query(Course).filter(Course.course_id == course_data.course_id).first()
    if existing_course:
        raise HTTPException(status_code=400, detail="Course ID already exists")

    db_course = Course(**course_data.dict(exclude={"subjects"}))
    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    # Add course subjects
    if course_data.subjects:
        for subject_data in course_data.subjects:
            # Tìm Subject dựa trên subject_id (string)
            subject = db.query(Subject).filter(Subject.subject_id == subject_data.subject_id).first()
            if not subject:
                raise HTTPException(status_code=404, detail=f"Subject with subject_id '{subject_data.subject_id}' not found")
            
            db_course_subject = CourseSubject(
                course_id=db_course.id,
                subject_id=subject.id,  # Sử dụng id (integer) của Subject
                subject_name=subject_data.subject_name
            )
            db.add(db_course_subject)
    db.commit()
    db.refresh(db_course)
    
    # Manually build response với subject_id string
    response_data = {
        "id": db_course.id,
        "course_id": db_course.course_id,
        "course_name": db_course.course_name,
        "course_subjects": []
    }
    
    for cs in db_course.course_subjects:
        response_data["course_subjects"].append({
            "subject_id": cs.subject.subject_id,  # String subject_id từ Subject
            "subject_name": cs.subject_name
        })
    
    return response_data


# ✅ Get all courses
@router.get("/", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    response_data = []
    
    for course in courses:
        course_data = {
            "id": course.id,
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_subjects": []
        }
        
        for cs in course.course_subjects:
            course_data["course_subjects"].append({
                "subject_id": cs.subject.subject_id,
                "subject_name": cs.subject_name
            })
        
        response_data.append(course_data)
    
    return response_data


# ✅ Get course by ID
@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course_data = {
        "id": course.id,
        "course_id": course.course_id,
        "course_name": course.course_name,
        "course_subjects": []
    }
    
    for cs in course.course_subjects:
        course_data["course_subjects"].append({
            "subject_id": cs.subject.subject_id,
            "subject_name": cs.subject_name
        })
    
    return course_data


# ✅ Update course
@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course_update: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for key, value in course_update.dict(exclude_unset=True, exclude={"subjects"}).items():
        setattr(course, key, value)

    # Update course subjects if provided
    if course_update.subjects is not None:
        db.query(CourseSubject).filter(CourseSubject.course_id == course.id).delete()
        for subject_data in course_update.subjects:
            # Tìm Subject dựa trên subject_id (string)
            subject = db.query(Subject).filter(Subject.subject_id == subject_data.subject_id).first()
            if not subject:
                raise HTTPException(status_code=404, detail=f"Subject with subject_id '{subject_data.subject_id}' not found")
            
            db_course_subject = CourseSubject(
                course_id=course.id,
                subject_id=subject.id,  # Sử dụng id (integer) của Subject
                subject_name=subject_data.subject_name
            )
            db.add(db_course_subject)

    db.commit()
    db.refresh(course)
    
    # Manual response building
    course_data = {
        "id": course.id,
        "course_id": course.course_id,
        "course_name": course.course_name,
        "course_subjects": []
    }
    
    for cs in course.course_subjects:
        course_data["course_subjects"].append({
            "subject_id": cs.subject.subject_id,
            "subject_name": cs.subject_name
        })
    
    return course_data


# ✅ Delete course
@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}


