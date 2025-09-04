from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.subject_model import Subject  # Sửa import
from app.schemas.subject_schema import SubjectCreate, SubjectUpdate, SubjectResponse
from typing import List, Optional

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# ✅ Create subject
@router.post("/", response_model=SubjectResponse)
def create_subject(subject_data: SubjectCreate, db: Session = Depends(get_db)):
    # Kiểm tra xem subject_id đã tồn tại chưa
    existing_subject = db.query(Subject).filter(Subject.subject_id == subject_data.subject_id).first()
    if existing_subject:
        raise HTTPException(status_code=400, detail="Subject ID already exists")
    
    
    
    db_subject = Subject(**subject_data.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

# ✅ Get all subjects
@router.get("/", response_model=List[SubjectResponse])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()

# ✅ Get subject by ID
@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: str, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

# ✅ Update subject
@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(subject_id: str, subject_update: SubjectUpdate, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    update_data = subject_update.dict(exclude_unset=True)
    
    # Xử lý conditional_subjects nếu có
    if 'conditional_subjects' in update_data:
        # Chuyển list thành string để lưu vào database
        update_data['conditional_subjects'] = ','.join(update_data['conditional_subjects']) if update_data['conditional_subjects'] else None
    
    for key, value in update_data.items():
        setattr(subject, key, value)

    db.commit()
    db.refresh(subject)
    return subject

# ✅ Delete subject
@router.delete("/{subject_id}")
def delete_subject(subject_id: str, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted successfully"}

# ✅ Get subject by subject_id (mã môn học)
@router.get("/by-code/{subject_code}", response_model=SubjectResponse)
def get_subject_by_code(subject_code: str, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.subject_id == subject_code).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject