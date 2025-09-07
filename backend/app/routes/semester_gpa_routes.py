from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import SemesterGPA
from app.schemas.semester_gpa_schema import SemesterGPACreate, SemesterGPAUpdate, SemesterGPAResponse

router = APIRouter(prefix="/semester-gpa", tags=["Semester GPA"])

# ✅ Create semester GPA
@router.post("/", response_model=SemesterGPAResponse)
def create_semester_gpa(semester_gpa_data: SemesterGPACreate, db: Session = Depends(get_db)):
    db_semester_gpa = SemesterGPA(**semester_gpa_data.dict())
    db.add(db_semester_gpa)
    db.commit()
    db.refresh(db_semester_gpa)
    return db_semester_gpa

# ✅ Get all semester GPAs
@router.get("/", response_model=list[SemesterGPAResponse])
def get_semester_gpas(db: Session = Depends(get_db)):
    return db.query(SemesterGPA).all()

# ✅ Get semester GPA by ID
@router.get("/{semester_gpa_id}", response_model=SemesterGPAResponse)
def get_semester_gpa(semester_gpa_id: int, db: Session = Depends(get_db)):
    semester_gpa = db.query(SemesterGPA).filter(SemesterGPA.id == semester_gpa_id).first()
    if not semester_gpa:
        raise HTTPException(status_code=404, detail="Semester GPA not found")
    return semester_gpa

# ✅ Update semester GPA
@router.put("/{semester_gpa_id}", response_model=SemesterGPAResponse)
def update_semester_gpa(semester_gpa_id: int, semester_gpa_update: SemesterGPAUpdate, db: Session = Depends(get_db)):
    semester_gpa = db.query(SemesterGPA).filter(SemesterGPA.id == semester_gpa_id).first()
    if not semester_gpa:
        raise HTTPException(status_code=404, detail="Semester GPA not found")

    for key, value in semester_gpa_update.dict(exclude_unset=True).items():
        setattr(semester_gpa, key, value)  # Update the attribute

    db.commit()
    db.refresh(semester_gpa)
    return semester_gpa

# ✅ Delete semester GPA
@router.delete("/{semester_gpa_id}")
def delete_semester_gpa(semester_gpa_id: int, db: Session = Depends(get_db)):
    semester_gpa = db.query(SemesterGPA).filter(SemesterGPA.id == semester_gpa_id).first()
    if not semester_gpa:
        raise HTTPException(status_code=404, detail="Semester GPA not found")
    db.delete(semester_gpa)
    db.commit()
    return {"message": "Semester GPA deleted successfully"}
