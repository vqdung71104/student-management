from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Class
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse

router = APIRouter(prefix="/classes", tags=["Classes"])

# ✅ Create class
@router.post("/", response_model=ClassResponse)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    # Convert data to dict and handle special fields
    class_dict = class_data.dict()
    
    # Convert linked_class_ids list to comma-separated string
    if class_dict["linked_class_ids"]:
        class_dict["linked_class_ids"] = ",".join(class_dict["linked_class_ids"])
    else:
        class_dict["linked_class_ids"] = ""
    
    # ❌ XÓA DÒNG NÀY - không cần convert enum nữa
    # if class_dict["class_type"]:
    #     class_dict["class_type"] = class_dict["class_type"].value
    
    db_class = Class(**class_dict)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

# ✅ Get all classes
@router.get("/", response_model=list[ClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()

# ✅ Get class by ID
@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj

# ✅ Update class
@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: int, class_update: ClassUpdate, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    update_dict = class_update.dict(exclude_unset=True)
    
    # Handle special fields
    for key, value in update_dict.items():
        if key == "linked_class_ids" and value is not None:
            if isinstance(value, list):
                value = ",".join(value) if value else ""
        # ❌ XÓA PHẦN NÀY - không cần convert enum nữa
        # elif key == "class_type" and value is not None:
        #     value = value.value
        
        setattr(class_obj, key, value)

    db.commit()
    db.refresh(class_obj)
    return class_obj

# ✅ Delete class
@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(class_obj)
    db.commit()
    return {"message": "Class deleted successfully"}
