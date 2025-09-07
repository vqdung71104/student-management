from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import ClassRegister
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
    return db.query(ClassRegister).all() # Return all class registers

# ✅ Get class register by ID
@router.get("/{register_id}", response_model=ClassRegisterResponse)
def get_class_register(register_id: int, db: Session = Depends(get_db)):
    register = db.query(ClassRegister).filter(ClassRegister.id == register_id).first()
    if not register:
        raise HTTPException(status_code=404, detail="Class register not found")
    return register

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
