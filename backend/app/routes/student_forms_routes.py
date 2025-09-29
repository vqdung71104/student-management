from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_model import Student
from app.models.notification_model import Notification
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/student-forms", tags=["Student Forms"])

class FormSubmissionRequest(BaseModel):
    student_id: str
    form_type: str
    form_content: str

class NotificationRequest(BaseModel):
    student_id: str
    title: str
    message: str
    type: str = "info"

@router.post("/submit")
def submit_form(
    request: FormSubmissionRequest,
    db: Session = Depends(get_db)
):
    """Submit a form and create notification"""
    try:
        # Verify student exists
        student = db.query(Student).filter(Student.student_id == request.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
        
        # Create notification
        notification = Notification(
            title=f"Đơn {request.form_type} đã được gửi",
            content=f"Đơn {request.form_type} của bạn đã được gửi thành công. Chúng tôi sẽ xử lý và phản hồi trong thời gian sớm nhất.",
            notification_type="form_submission",
            target_type="student",
            target_id=request.student_id,
            created_at=datetime.now()
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return {
            "message": "Biểu mẫu đã được gửi thành công",
            "notification_id": notification.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.post("/notification")
def create_notification(
    request: NotificationRequest,
    db: Session = Depends(get_db)
):
    """Create a notification for student"""
    try:
        # Verify student exists
        student = db.query(Student).filter(Student.student_id == request.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
        
        # Create notification
        notification = Notification(
            title=request.title,
            content=request.message,
            notification_type=request.type,
            target_type="student",
            target_id=request.student_id,
            created_at=datetime.now()
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return {
            "message": "Thông báo đã được tạo thành công",
            "notification_id": notification.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
