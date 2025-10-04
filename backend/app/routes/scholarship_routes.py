from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.scholarship_model import Scholarship
from app.schemas.scholarship_schema import (
    ScholarshipCreate,
    ScholarshipUpdate,
    ScholarshipResponse,
    ScholarshipListResponse
)


router = APIRouter(prefix="/api/scholarships", tags=["Scholarships"])


@router.get("/", response_model=List[ScholarshipListResponse])
async def get_scholarships(
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách học bổng
    """
    try:
        query = db.query(Scholarship)
        
        if search:
            query = query.filter(
                Scholarship.title.contains(search) |
                Scholarship.sponsor.contains(search)
            )
        
        if type_filter:
            query = query.filter(Scholarship.type == type_filter)
        
        scholarships = query.order_by(desc(Scholarship.created_at)).all()
        return scholarships
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi server: {str(e)}"
        )


@router.get("/{scholarship_id}", response_model=ScholarshipResponse)
async def get_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết học bổng
    """
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học bổng"
        )
    return scholarship


@router.post("/", response_model=ScholarshipResponse)
async def create_scholarship(
    scholarship_data: ScholarshipCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo học bổng mới
    """
    try:
        scholarship = Scholarship(**scholarship_data.dict())
        
        db.add(scholarship)
        db.commit()
        db.refresh(scholarship)
        
        return scholarship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tạo học bổng: {str(e)}"
        )


@router.put("/{scholarship_id}", response_model=ScholarshipResponse)
async def update_scholarship(
    scholarship_id: int,
    scholarship_data: ScholarshipUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin học bổng
    """
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học bổng"
        )
    
    try:
        for field, value in scholarship_data.dict(exclude_unset=True).items():
            setattr(scholarship, field, value)
        
        scholarship.updated_at = datetime.now()
        db.commit()
        db.refresh(scholarship)
        
        return scholarship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi cập nhật học bổng: {str(e)}"
        )


@router.delete("/{scholarship_id}")
async def delete_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db)
):
    """
    Xóa học bổng
    """
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học bổng"
        )
    
    try:
        db.delete(scholarship)
        db.commit()
        
        return {"success": True, "message": "Xóa học bổng thành công"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xóa học bổng: {str(e)}"
        )


@router.post("/{scholarship_id}/upload-document")
async def upload_document(
    scholarship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload tài liệu cho học bổng
    """
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học bổng"
        )
    
    try:
        # Lưu file (implementation tùy vào storage system)
        # Ví dụ đơn giản: lưu tên file vào database
        scholarship.document_url = file.filename
        db.commit()
        
        return {
            "success": True,
            "message": "Upload tài liệu thành công",
            "document_url": scholarship.document_url
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi upload tài liệu: {str(e)}"
        )