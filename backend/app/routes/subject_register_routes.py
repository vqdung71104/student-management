from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import SubjectRegister, Subject
from app.schemas.subject_register_schema import SubjectRegisterCreate, SubjectRegisterUpdate, SubjectRegisterResponse

router = APIRouter(prefix="/subject-registers", tags=["Subject Registers"])

#    Create subject register
@router.post("/", response_model=SubjectRegisterResponse)
def create_subject_register(subject_register_data: SubjectRegisterCreate, db: Session = Depends(get_db)):
    # Lấy subject từ subject_id
    subject = db.query(Subject).filter(Subject.id == subject_register_data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Tạo bản ghi mới, tự động thêm subject_name và credits
    db_subject_register = SubjectRegister(
        student_id=subject_register_data.student_id,
        subject_id=subject_register_data.subject_id,
        subject_name=subject.subject_name,
        credits=subject.credits
    )

    db.add(db_subject_register)
    db.commit()
    db.refresh(db_subject_register)
    return db_subject_register

#    Get all subject registers
@router.get("/", response_model=list[SubjectRegisterResponse])
def get_subject_registers(db: Session = Depends(get_db)):
    return db.query(SubjectRegister).all()

#    Get subject register by ID
@router.get("/{subject_register_id}", response_model=SubjectRegisterResponse)
def get_subject_register(subject_register_id: int, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")
    return subject_register

#    Get subject registers by student ID
@router.get("/student/{student_id}", response_model=list[SubjectRegisterResponse])
def get_subject_registers_by_student(student_id: int, db: Session = Depends(get_db)):
    subject_registers = db.query(SubjectRegister).filter(SubjectRegister.student_id == student_id).all()
    return subject_registers

#    Get subject registers by student MSSV
@router.get("/student-mssv/{mssv}", response_model=list[SubjectRegisterResponse])
def get_subject_registers_by_mssv(mssv: str, db: Session = Depends(get_db)):
    # First get student by student_id (MSSV)
    from ..models.student_model import Student
    student = db.query(Student).filter(Student.student_id == mssv).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Then get subject registers by student's database ID
    subject_registers = db.query(SubjectRegister).filter(SubjectRegister.student_id == student.id).all()
    return subject_registers

#    Update subject register (chỉ được đổi student_id hoặc subject_id, còn subject_name và credits sẽ cập nhật lại theo subject mới)
@router.put("/{subject_register_id}", response_model=SubjectRegisterResponse)
def update_subject_register(subject_register_id: int, subject_register_update: SubjectRegisterUpdate, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")

    if subject_register_update.student_id is not None:
        subject_register.student_id = subject_register_update.student_id

    if subject_register_update.subject_id is not None:
        subject = db.query(Subject).filter(Subject.id == subject_register_update.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        subject_register.subject_id = subject_register_update.subject_id
        subject_register.subject_name = subject.subject_name
        subject_register.credits = subject.credits

    db.commit()
    db.refresh(subject_register)
    return subject_register

#    Delete subject register
@router.delete("/{subject_register_id}")
def delete_subject_register(subject_register_id: int, db: Session = Depends(get_db)):
    subject_register = db.query(SubjectRegister).filter(SubjectRegister.id == subject_register_id).first()
    if not subject_register:
        raise HTTPException(status_code=404, detail="Subject register not found")
    db.delete(subject_register)
    db.commit()
    return {"message": "Subject register deleted successfully"}
