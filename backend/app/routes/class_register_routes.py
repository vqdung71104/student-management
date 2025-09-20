from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.__init__ import ClassRegister, Student
from app.schemas.class_register_schema import ClassRegisterCreate, ClassRegisterUpdate, ClassRegisterResponse

router = APIRouter(prefix="/class-registers", tags=["Class Registers"])

# ✅ Create class register
@router.post("/", response_model=ClassRegisterResponse)
def create_class_register(register_data: ClassRegisterCreate, db: Session = Depends(get_db)):
    db_register = ClassRegister(**register_data.dict())
    db.add(db_register)
    db.commit()
    db.refresh(db_register)
    return db_register

# ✅ Get all class registers
@router.get("/", response_model=list[ClassRegisterResponse])
def get_class_registers(db: Session = Depends(get_db)):
    return db.query(ClassRegister).all()

# ✅ Get class register by ID
@router.get("/{register_id}", response_model=ClassRegisterResponse)
def get_class_register(register_id: int, db: Session = Depends(get_db)):
    register = db.query(ClassRegister).filter(ClassRegister.id == register_id).first()
    if not register:
        raise HTTPException(status_code=404, detail="Class register not found")
    return register

# ✅ Get class registers by student database ID (internal ID)
@router.get("/student/{student_id}", response_model=list[ClassRegisterResponse])
def get_class_registers_by_student_db_id(student_id: int, db: Session = Depends(get_db)):
    registers = db.query(ClassRegister).filter(ClassRegister.student_id == student_id).all()
    return registers

# ✅ Get class registers by student MSSV
@router.get("/student-mssv/{student_id}", response_model=List[ClassRegisterResponse])
def get_class_registers_by_student_mssv(student_id: str, db: Session = Depends(get_db)):
    """Get all class registers for a student by student_id (MSSV)"""
    # First find the student by student_id
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Then get class registers by student's database ID
    registers = db.query(ClassRegister)\
        .filter(ClassRegister.student_id == student.id)\
        .all()
    return registers

@router.get("/student-by-id/{student_db_id}", response_model=List[ClassRegisterResponse])
def get_class_registers_by_student_id(student_db_id: int, db: Session = Depends(get_db)):
    registers = db.query(ClassRegister).filter(ClassRegister.student_id == student_db_id).all()
    return registers

# ✅ Get class registers by class ID
@router.get("/class/{class_id}", response_model=list[ClassRegisterResponse])
def get_class_registers_by_class(class_id: int, db: Session = Depends(get_db)):
    registers = db.query(ClassRegister).filter(ClassRegister.class_id == class_id).all()
    return registers

# ✅ Update class register
@router.put("/{register_id}", response_model=ClassRegisterResponse)
def update_class_register(register_id: int, register_update: ClassRegisterUpdate, db: Session = Depends(get_db)):
    register = db.query(ClassRegister).filter(ClassRegister.id == register_id).first()
    if not register:
        raise HTTPException(status_code=404, detail="Class register not found")

    for key, value in register_update.dict(exclude_unset=True).items():
        setattr(register, key, value)

    db.commit()
    db.refresh(register)
    return register

# ✅ Delete class register
@router.delete("/{register_id}")
def delete_class_register(register_id: int, db: Session = Depends(get_db)):
    register = db.query(ClassRegister).filter(ClassRegister.id == register_id).first()
    if not register:
        raise HTTPException(status_code=404, detail="Class register not found")
    db.delete(register)
    db.commit()
    return {"message": "Class register deleted successfully"}
