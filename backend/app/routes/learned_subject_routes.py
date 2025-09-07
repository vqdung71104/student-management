from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import LearnedSubject, Subject
from app.schemas.learned_subject_schema import (
    LearnedSubjectCreate,
    LearnedSubjectUpdate,
    LearnedSubjectResponse,
)

router = APIRouter(prefix="/learned-subjects", tags=["Learned Subjects"])


# 🔹 Hàm tính grade
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


# ✅ Create learned subject
@router.post("/", response_model=LearnedSubjectResponse)
def create_learned_subject(
    learned_subject_data: LearnedSubjectCreate, db: Session = Depends(get_db)
):
    # Lấy thông tin môn học từ bảng Subject
    subject = db.query(Subject).filter(Subject.id == learned_subject_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Làm tròn final_score
    final_score = round(learned_subject_data.final_score, 1)

    # Tính total_score
    total_score = final_score * learned_subject_data.weight + learned_subject_data.midterm_score * (
        1 - learned_subject_data.weight
    )

    # Tính letter grade
    letter_grade = calculate_letter_grade(final_score)

    db_learned_subject = LearnedSubject(
        subject_name=subject.subject_name,
        credits=subject.credits,
        final_score=final_score,
        midterm_score=learned_subject_data.midterm_score,
        weight=learned_subject_data.weight,
        total_score=round(total_score, 1),
        letter_grade=letter_grade,
        semester=learned_subject_data.semester,
        student_id=learned_subject_data.student_id,
        subject_id=learned_subject_data.subject_id,
    )

    db.add(db_learned_subject)
    db.commit()
    db.refresh(db_learned_subject)
    return db_learned_subject


# ✅ Get all learned subjects
@router.get("/", response_model=list[LearnedSubjectResponse])
def get_learned_subjects(db: Session = Depends(get_db)):
    return db.query(LearnedSubject).all()


# ✅ Get learned subject by ID
@router.get("/{learned_subject_id}", response_model=LearnedSubjectResponse)
def get_learned_subject(learned_subject_id: int, db: Session = Depends(get_db)):
    learned_subject = (
        db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    )
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    return learned_subject


# ✅ Update learned subject
@router.put("/{learned_subject_id}", response_model=LearnedSubjectResponse)
def update_learned_subject(
    learned_subject_id: int,
    learned_subject_update: LearnedSubjectUpdate,
    db: Session = Depends(get_db),
):
    learned_subject = (
        db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    )
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")

    # Update các field cho phép
    for key, value in learned_subject_update.dict(exclude_unset=True).items():
        setattr(learned_subject, key, value)

    # Nếu có cập nhật final_score/midterm/weight thì tính lại
    if (
        learned_subject_update.final_score is not None
        or learned_subject_update.midterm_score is not None
        or learned_subject_update.weight is not None
    ):
        learned_subject.final_score = round(learned_subject.final_score, 1)
        learned_subject.total_score = round(
            learned_subject.final_score * learned_subject.weight
            + learned_subject.midterm_score * (1 - learned_subject.weight),
            1,
        )
        learned_subject.letter_grade = calculate_letter_grade(
            learned_subject.final_score
        )

    db.commit()
    db.refresh(learned_subject)
    return learned_subject


# ✅ Delete learned subject
@router.delete("/{learned_subject_id}")
def delete_learned_subject(learned_subject_id: int, db: Session = Depends(get_db)):
    learned_subject = (
        db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    )
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    db.delete(learned_subject)
    db.commit()
    return {"message": "Learned subject deleted successfully"}
