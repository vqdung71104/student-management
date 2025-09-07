from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.models.__init__ import LearnedSubject, Subject, Student, SemesterGPA
from app.schemas.learned_subject_schema import (
    LearnedSubjectCreate,
    LearnedSubjectUpdate,
    LearnedSubjectResponse,
)

router = APIRouter(prefix="/learned-subjects", tags=["Learned Subjects"])

# 🔹 Hàm tính letter grade to score (thang 4.0)
def letter_grade_to_score(letter_grade: str) -> float:
    grade_map = {
        "F": 0.0,
        "D": 1.0,
        "D+": 1.5,
        "C": 2.0,
        "C+": 2.5,
        "B": 3.0,
        "B+": 3.5,
        "A": 4.0,
        "A+": 4.0
    }
    return grade_map.get(letter_grade, 0.0)

# 🔹 Hàm tính letter grade từ điểm số
def calculate_letter_grade(score: float) -> str:
    if 0.0 <= score <= 3.9:
        return "F"
    elif 4.0 <= score <= 4.9:
        return "D"
    elif 5.0 <= score <= 5.4:
        return "D+"
    elif 5.5 <= score <= 6.4:
        return "C"
    elif 6.5 <= score <= 6.9:
        return "C+"
    elif 7.0 <= score <= 7.9:
        return "B"
    elif 8.0 <= score <= 8.4:
        return "B+"
    elif 8.5 <= score <= 9.4:
        return "A"
    elif 9.5 <= score <= 10.0:
        return "A+"
    return "F"

# 🔹 Hàm update semester GPA
def update_semester_gpa(student_id: int, semester: str, db: Session):
    # Lấy tất cả learned subjects của student trong semester này
    learned_subjects = db.query(LearnedSubject).filter(
        and_(
            LearnedSubject.student_id == student_id,
            LearnedSubject.semester == semester
        )
    ).all()
    
    if not learned_subjects:
        return
    
    total_credits = 0
    total_grade_points = 0.0
    
    for ls in learned_subjects:
        credits = ls.credits
        score = letter_grade_to_score(ls.letter_grade)
        total_credits += credits
        total_grade_points += credits * score
    
    gpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    
    # Tìm hoặc tạo semester GPA
    semester_gpa = db.query(SemesterGPA).filter(
        and_(
            SemesterGPA.student_id == student_id,
            SemesterGPA.semester == semester
        )
    ).first()
    
    if semester_gpa:
        semester_gpa.gpa = gpa
        semester_gpa.total_credits = total_credits
    else:
        semester_gpa = SemesterGPA(
            student_id=student_id,
            semester=semester,
            gpa=gpa,
            total_credits=total_credits
        )
        db.add(semester_gpa)

# 🔹 Hàm update student stats
def update_student_stats(student_id: int, db: Session):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return
    
    # Lấy tất cả learned subjects của student
    learned_subjects = db.query(LearnedSubject).filter(LearnedSubject.student_id == student_id).all()
    
    # Reset counters
    failed_subjects_number = 0
    study_subjects_number = 0
    total_failed_credits = 0
    total_learned_credits = 0
    
    for ls in learned_subjects:
        if ls.letter_grade == "F":
            failed_subjects_number += 1
            total_failed_credits += ls.credits
        else:
            study_subjects_number += 1
            total_learned_credits += ls.credits
    
    # Update student fields
    student.failed_subjects_number = failed_subjects_number
    student.study_subjects_number = study_subjects_number
    student.total_failed_credits = total_failed_credits
    student.total_learned_credits = total_learned_credits
    
    # Calculate CPA from all semester GPAs
    semester_gpas = db.query(SemesterGPA).filter(SemesterGPA.student_id == student_id).all()
    total_credits = sum(sgpa.total_credits for sgpa in semester_gpas)
    total_grade_points = sum(sgpa.gpa * sgpa.total_credits for sgpa in semester_gpas)
    
    student.cpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    
    # Update warning level
    old_warning = student.warning_level
    if total_failed_credits >= 27:
        student.warning_level = "Cảnh báo mức 3"
    elif total_failed_credits >= 16:
        student.warning_level = "Cảnh báo mức 2"
    elif total_failed_credits >= 8:
        student.warning_level = "Cảnh báo mức 1"
    else:
        student.warning_level = "Cảnh báo mức 0"
    
    # Update level 3 warning counter
    if old_warning != "Cảnh báo mức 3" and student.warning_level == "Cảnh báo mức 3":
        student.level_3_warning_number += 1
    
    # Update year level
    total_learned = total_learned_credits
    if total_learned < 32:
        student.year_level = "Năm 1"
    elif total_learned < 64:
        student.year_level = "Năm 2"
    elif total_learned < 96:
        student.year_level = "Năm 3"
    elif total_learned < 128:
        student.year_level = "Năm 4"
    else:
        student.year_level = "Năm 5"

# 🔹 CRUD ROUTES

@router.get("/", response_model=list[LearnedSubjectResponse])
def get_all_learned_subjects(db: Session = Depends(get_db)):
    learned_subjects = db.query(LearnedSubject).all()
    return learned_subjects

@router.get("/{learned_subject_id}", response_model=LearnedSubjectResponse)
def get_learned_subject(learned_subject_id: int, db: Session = Depends(get_db)):
    learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    return learned_subject

@router.get("/student/{student_id}", response_model=list[LearnedSubjectResponse])
def get_learned_subjects_by_student(student_id: int, db: Session = Depends(get_db)):
    learned_subjects = db.query(LearnedSubject).filter(LearnedSubject.student_id == student_id).all()
    return learned_subjects

@router.get("/student/{student_id}/semester/{semester}", response_model=list[LearnedSubjectResponse])
def get_learned_subjects_by_student_and_semester(
    student_id: int, 
    semester: str, 
    db: Session = Depends(get_db)
):
    learned_subjects = db.query(LearnedSubject).filter(
        and_(
            LearnedSubject.student_id == student_id,
            LearnedSubject.semester == semester
        )
    ).all()
    return learned_subjects

@router.post("/", response_model=LearnedSubjectResponse)
def create_learned_subject(learned_subject: LearnedSubjectCreate, db: Session = Depends(get_db)):
    # Get subject info
    subject = db.query(Subject).filter(Subject.id == learned_subject.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Calculate total score
    final_score = round(learned_subject.final_score, 1)
    total_score = final_score * learned_subject.weight + learned_subject.midterm_score * (1 - learned_subject.weight)
    
    # Auto-calculate letter grade from final score
    letter_grade = calculate_letter_grade(final_score)
    
    # Create learned subject
    db_learned_subject = LearnedSubject(
        subject_name=subject.subject_name,
        credits=subject.credits,
        final_score=final_score,
        midterm_score=learned_subject.midterm_score,
        weight=learned_subject.weight,
        total_score=round(total_score, 1),
        letter_grade=letter_grade,
        semester=learned_subject.semester,
        student_id=learned_subject.student_id,
        subject_id=learned_subject.subject_id
    )
    
    db.add(db_learned_subject)
    db.commit()
    db.refresh(db_learned_subject)
    
    # 🎯 AUTO-CALCULATE GPA & STUDENT STATS
    update_semester_gpa(db_learned_subject.student_id, db_learned_subject.semester, db)
    update_student_stats(db_learned_subject.student_id, db)
    db.commit()
    
    return db_learned_subject

@router.put("/{learned_subject_id}", response_model=LearnedSubjectResponse)
def update_learned_subject(
    learned_subject_id: int, 
    learned_subject: LearnedSubjectUpdate, 
    db: Session = Depends(get_db)
):
    db_learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not db_learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    
    # Update fields
    for field, value in learned_subject.model_dump(exclude_unset=True).items():
        setattr(db_learned_subject, field, value)
    
    # Recalculate if final_score, midterm_score, or weight changed
    if (learned_subject.final_score is not None or 
        learned_subject.midterm_score is not None or 
        learned_subject.weight is not None):
        
        db_learned_subject.final_score = round(db_learned_subject.final_score, 1)
        db_learned_subject.total_score = round(
            db_learned_subject.final_score * db_learned_subject.weight + 
            db_learned_subject.midterm_score * (1 - db_learned_subject.weight), 1
        )
        db_learned_subject.letter_grade = calculate_letter_grade(db_learned_subject.final_score)
    
    db.commit()
    db.refresh(db_learned_subject)
    
    # 🎯 AUTO-CALCULATE GPA & STUDENT STATS
    update_semester_gpa(db_learned_subject.student_id, db_learned_subject.semester, db)
    update_student_stats(db_learned_subject.student_id, db)
    db.commit()
    
    return db_learned_subject

@router.delete("/{learned_subject_id}")
def delete_learned_subject(learned_subject_id: int, db: Session = Depends(get_db)):
    db_learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not db_learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    
    student_id = db_learned_subject.student_id
    semester = db_learned_subject.semester
    
    db.delete(db_learned_subject)
    db.commit()
    
    # 🎯 AUTO-CALCULATE GPA & STUDENT STATS after deletion
    update_semester_gpa(student_id, semester, db)
    update_student_stats(student_id, db)
    db.commit()
    
    return {"message": "Learned subject deleted successfully"}
