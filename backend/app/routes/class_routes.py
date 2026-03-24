from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.__init__ import Class, ClassRegister
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import text

router = APIRouter(prefix="/classes", tags=["Classes"])

# Schema for teacher update
class TeacherUpdate(BaseModel):
    class_id: str
    class_id_kem: str
    teacher: str

class TeacherUpdateRequest(BaseModel):
    updates: List[TeacherUpdate]

#    Create class
@router.post("/", response_model=ClassResponse)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    # Convert data to dict and handle special fields
    class_dict = class_data.dict()
    
    # Convert linked_class_ids list to comma-separated string
    if class_dict["linked_class_ids"]:
        class_dict["linked_class_ids"] = ",".join(class_dict["linked_class_ids"])
    else:
        class_dict["linked_class_ids"] = ""
    
    try:
        db_class = Class(**class_dict)
        db.add(db_class)
        db.commit()
        db.refresh(db_class)
        return db_class
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#    Delete single class by ID (under actions namespace)
@router.delete("/actions/delete/{class_id}")
def delete_class_action(class_id: int, db: Session = Depends(get_db)):
    try:
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        db.delete(class_obj)
        db.commit()
        return {"message": "Class deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete class: {str(e)}")


def _purge_all_classes(db: Session):
    # Temporary import mode: allow duplicate class_id values from Excel rows.
    unique_indexes = db.execute(text("""
        SELECT INDEX_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'classes'
          AND COLUMN_NAME = 'class_id'
          AND NON_UNIQUE = 0
          AND INDEX_NAME <> 'PRIMARY'
    """)).fetchall()

    for row in unique_indexes:
        index_name = row[0]
        db.execute(text(f"ALTER TABLE classes DROP INDEX `{index_name}`"))

    deleted_registers = db.query(ClassRegister).delete(synchronize_session=False)
    deleted_classes = db.query(Class).delete(synchronize_session=False)
    db.commit()
    return {
        "message": "Purged all class registrations and classes successfully",
        "deleted_class_registers": deleted_registers,
        "deleted_classes": deleted_classes,
    }


#    Purge all classes (accept both slash/no-slash)
@router.delete("/actions/purge-all")
@router.delete("/actions/purge-all/", include_in_schema=False)
def purge_all_classes(db: Session = Depends(get_db)):
    try:
        return _purge_all_classes(db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to purge classes: {str(e)}")

#    Get all classes
@router.get("/", response_model=list[ClassResponse])
def get_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()

#    Get class by ID
@router.get("/{class_id:int}", response_model=ClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj

#    Update class
@router.put("/{class_id:int}", response_model=ClassResponse)
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
        #   XÓA PHẦN NÀY - không cần convert enum nữa
        # elif key == "class_type" and value is not None:
        #     value = value.value
        
        setattr(class_obj, key, value)

    db.commit()
    db.refresh(class_obj)
    return class_obj

#    Delete class
@router.delete("/{class_id:int}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(class_obj)
    db.commit()
    return {"message": "Class deleted successfully"}

#    Update teachers from Excel
@router.post("/update-teachers")
def update_teachers(request: TeacherUpdateRequest, db: Session = Depends(get_db)):
    """Update teacher names for existing classes based on class_id"""
    updated_count = 0
    errors = []
    
    for update in request.updates:
        try:
            # Tìm lớp dựa trên class_id hoặc class_id_kem
            class_obj = db.query(Class).filter(
                (Class.class_id == update.class_id)  
               
            ).first()
            
            if class_obj:
                # Cập nhật tên giáo viên
                class_obj.teacher_name = update.teacher
                print(f"Updating class {class_obj.class_id} with teacher {update.teacher}")
                updated_count += 1
            else:
                errors.append(f"Không tìm thấy lớp với mã: {update.class_id} hoặc {update.class_id_kem}")
                
        except Exception as e:
            errors.append(f"Lỗi khi cập nhật lớp {update.class_id}: {str(e)}")
    
    try:
        db.commit()
        
        result = {
            "updated_count": updated_count,
            "total_records": len(request.updates),
            "message": f"Đã cập nhật thành công {updated_count}/{len(request.updates)} lớp"
        }
        
        if errors:
            result["errors"] = errors
            
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu dữ liệu: {str(e)}")
