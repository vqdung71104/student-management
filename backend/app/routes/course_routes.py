from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Course, CourseSubject, Subject, Student, LearnedSubject
from app.schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


#    Create course
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
                learning_semester=subject_data.learning_semester  # Thêm learning_semester
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
            "learning_semester": cs.learning_semester  # Thêm learning_semester
        })
    
    return response_data


#    Get all courses
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
                "learning_semester": cs.learning_semester  # Thêm learning_semester
            })
        
        response_data.append(course_data)
    
    return response_data


#    Get course by ID
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
            "learning_semester": cs.learning_semester  # Thêm learning_semester
        })
    
    return course_data


#    Update course
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
                learning_semester=subject_data.learning_semester  # Thêm learning_semester
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
            "learning_semester": cs.learning_semester  # Thêm learning_semester
        })
    
    return course_data


#    Delete course
@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}


#    Get student curriculum - course and subjects with learned status
@router.get("/{student_id}/curriculum")
def get_student_curriculum(student_id: str, db: Session = Depends(get_db)):
    # Find student by student_id (string)
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's course
    course = db.query(Course).filter(Course.id == student.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found for this student")
    
    # Get all subjects in the course
    course_subjects = db.query(CourseSubject).filter(CourseSubject.course_id == course.id).all()
    
    # Get student's learned subjects 
    learned_subjects = db.query(LearnedSubject).filter(LearnedSubject.student_id == student.id).all()
    learned_subjects_dict = {ls.subject_id: ls for ls in learned_subjects}
    
    # Build curriculum data
    curriculum_subjects = []
    for cs in course_subjects:
        subject = db.query(Subject).filter(Subject.id == cs.subject_id).first()
        if subject:
            learned_data = learned_subjects_dict.get(subject.id)
            curriculum_subjects.append({
                "subject_id": subject.subject_id,
                "subject_name": subject.subject_name,
                "credits": subject.credits,
                "letter_grade": learned_data.letter_grade if learned_data else None,
                "semester": learned_data.semester if learned_data else None,
                "is_completed": learned_data is not None
            })
    
    return {
        "course_id": course.course_id,
        "course_name": course.course_name,
        "subjects": curriculum_subjects,
        "total_subjects": len(curriculum_subjects),
        "completed_subjects": len([s for s in curriculum_subjects if s["is_completed"]])
    }


