from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import SubjectRegister
from app.schemas.subject_register_schema import SubjectRegisterCreate, SubjectRegisterUpdate, SubjectRegisterResponse

router = APIRouter(prefix="/subject-registers", tags=["Subject Registers"])

# ✅ Create subject register
@router.post("/", response_model=SubjectRegisterResponse)
def create_subject_register(subject_register_data: SubjectRegisterCreate, db: Session = Depends(get_db)):
    db_subject_register = SubjectRegister(**subject_register_data.dict())
    db.add(db_subject_register)
    db.commit()
    db.refresh(db_subject_register)
    return db_subject_register

# ✅ Get all subject registers
@router.get("/", response_model=list[SubjectRegisterResponse])
def get_subject_registers(db: Session = Depends(get_db)):
    return db.query(SubjectRegister).all()

# ✅ Get subject register by ID
@router.get("/{subject_register_id}", response_model=SubjectRegisterResponse)
def get_subject_register(subject_register_id: int, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")
    return subject_register

# ✅ Update subject register
@router.put("/{subject_register_id}", response_model=SubjectRegisterResponse)
def update_subject_register(subject_register_id: int, subject_register_update: SubjectRegisterUpdate, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")

    for key, value in subject_register_update.dict(exclude_unset=True).items():
        setattr(subject_register, key, value)

    db.commit()
    db.refresh(subject_register)
    return subject_register

# ✅ Delete subject register
@router.delete("/{subject_register_id}")
def delete_subject_register(subject_register_id: int, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")
    db.delete(subject_register)
    db.commit()
    return {"message": "Subject register deleted successfully"}
