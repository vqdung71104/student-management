from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_drl_model import StudentDRL
from app.models.student_model import Student
from app.schemas.student_drl_schema import StudentDRLCreate, StudentDRLUpdate, StudentDRLResponse
from typing import List, Optional

router = APIRouter(prefix="/student-drl", tags=["Student DRL"])


@router.get("/", response_model=List[StudentDRLResponse])
def get_all_student_drl(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    semester: Optional[int] = Query(None, description="Filter by semester"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """Lấy danh sách điểm rèn luyện"""
    query = db.query(StudentDRL)
    
    if student_id:
        query = query.filter(StudentDRL.student_id == student_id)
    if semester:
        query = query.filter(StudentDRL.semester == semester)
    
    drl_records = query.offset(skip).limit(limit).all()
    return drl_records


@router.get("/{drl_id}", response_model=StudentDRLResponse)
def get_student_drl(drl_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin điểm rèn luyện theo ID"""
    drl_record = db.query(StudentDRL).filter(StudentDRL.id == drl_id).first()
    if not drl_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi điểm rèn luyện")
    return drl_record


@router.post("/", response_model=StudentDRLResponse)
def create_student_drl(drl_data: StudentDRLCreate, db: Session = Depends(get_db)):
    """Tạo mới điểm rèn luyện"""
    # Kiểm tra student_id có tồn tại không
    student = db.query(Student).filter(Student.student_id == drl_data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    
    # Kiểm tra xem sinh viên đã có điểm rèn luyện cho kỳ này chưa
    existing_drl = db.query(StudentDRL).filter(
        StudentDRL.student_id == drl_data.student_id,
        StudentDRL.semester == drl_data.semester
    ).first()
    
    if existing_drl:
        raise HTTPException(
            status_code=400, 
            detail=f"Sinh viên {drl_data.student_id} đã có điểm rèn luyện cho kỳ {drl_data.semester}"
        )
    
    new_drl = StudentDRL(**drl_data.dict())
    db.add(new_drl)
    db.commit()
    db.refresh(new_drl)
    return new_drl


@router.put("/{drl_id}", response_model=StudentDRLResponse)
def update_student_drl(drl_id: int, drl_data: StudentDRLUpdate, db: Session = Depends(get_db)):
    """Cập nhật điểm rèn luyện"""
    drl_record = db.query(StudentDRL).filter(StudentDRL.id == drl_id).first()
    if not drl_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi điểm rèn luyện")
    
    update_data = drl_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drl_record, field, value)
    
    db.commit()
    db.refresh(drl_record)
    return drl_record


@router.delete("/{drl_id}")
def delete_student_drl(drl_id: int, db: Session = Depends(get_db)):
    """Xóa điểm rèn luyện"""
    drl_record = db.query(StudentDRL).filter(StudentDRL.id == drl_id).first()
    if not drl_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi điểm rèn luyện")
    
    db.delete(drl_record)
    db.commit()
    return {"message": f"Đã xóa điểm rèn luyện ID {drl_id}"}


@router.get("/student/{student_id}/summary")
def get_student_drl_summary(student_id: str, db: Session = Depends(get_db)):
    """Lấy tóm tắt điểm rèn luyện của sinh viên"""
    # Kiểm tra sinh viên tồn tại
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    
    drl_records = db.query(StudentDRL).filter(StudentDRL.student_id == student_id).all()
    
    if not drl_records:
        return {
            "student_id": student_id,
            "total_semesters": 0,
            "average_drl": 0,
            "highest_drl": None,
            "lowest_drl": None,
            "records": []
        }
    
    drl_scores = [record.drl_score for record in drl_records]
    
    return {
        "student_id": student_id,
        "total_semesters": len(drl_records),
        "average_drl": round(sum(drl_scores) / len(drl_scores), 2),
        "highest_drl": max(drl_scores),
        "lowest_drl": min(drl_scores),
        "records": drl_records
    }