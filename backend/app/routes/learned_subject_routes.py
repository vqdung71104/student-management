from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import LearnedSubject
from app.schemas.learned_subject_schema import LearnedSubjectCreate, LearnedSubjectUpdate, LearnedSubjectResponse

router = APIRouter(prefix="/learned-subjects", tags=["Learned Subjects"])

# ✅ Create learned subject
@router.post("/", response_model=LearnedSubjectResponse)
def create_learned_subject(learned_subject_data: LearnedSubjectCreate, db: Session = Depends(get_db)):
    db_learned_subject = LearnedSubject(**learned_subject_data.dict())
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
    learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    return learned_subject

# ✅ Update learned subject
@router.put("/{learned_subject_id}", response_model=LearnedSubjectResponse)
def update_learned_subject(learned_subject_id: int, learned_subject_update: LearnedSubjectUpdate, db: Session = Depends(get_db)):
    learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")

    for key, value in learned_subject_update.dict(exclude_unset=True).items():
        setattr(learned_subject, key, value)

    db.commit()
    db.refresh(learned_subject)
    return learned_subject

# ✅ Delete learned subject
@router.delete("/{learned_subject_id}")
def delete_learned_subject(learned_subject_id: int, db: Session = Depends(get_db)):
    learned_subject = db.query(LearnedSubject).filter(LearnedSubject.id == learned_subject_id).first()
    if not learned_subject:
        raise HTTPException(status_code=404, detail="Learned subject not found")
    db.delete(learned_subject)
    db.commit()
    return {"message": "Learned subject deleted successfully"}
