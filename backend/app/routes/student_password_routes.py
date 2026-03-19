from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_model import Student
from app.utils.jwt_utils import get_current_student
from app.schemas.student_schemas import (
    StudentChangePasswordRequest, 
    StudentRequestPasswordResetRequest, 
    StudentVerifyOTPRequest,
    StudentPasswordResetResponse
)
from app.services.email_service import email_service
from pydantic import BaseModel, validator
import hashlib
import re
from datetime import datetime

router = APIRouter(prefix="/student", tags=["Student Password Management"])


def hash_password_sha256(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password_md5(password: str) -> str:
    """Hash password using MD5 (for backward compatibility)"""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash (support both MD5 and SHA256)"""
    # Try SHA256 first (new format)
    if hash_password_sha256(password) == hashed_password:
        return True
    # Fallback to MD5 (old format)
    return hash_password_md5(password) == hashed_password


@router.post("/request-password-reset", response_model=StudentPasswordResetResponse)
def request_password_reset(
    request: StudentRequestPasswordResetRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Deprecated OTP flow: endpoint kept for backward compatibility."""
    return StudentPasswordResetResponse(
        message="OTP flow is disabled. Use /student/change-password while authenticated.",
        expires_in=0,
    )


@router.post("/verify-otp-and-change-password")
def verify_otp_and_change_password(
    request: StudentVerifyOTPRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Deprecated OTP flow: endpoint kept for backward compatibility."""
    raise HTTPException(
        status_code=410,
        detail="OTP flow is disabled. Use /student/change-password while authenticated.",
    )


class StudentChangePasswordWithEmailRequest(BaseModel):
    student_email: str
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Kiểm tra mật khẩu mạnh"""
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết hoa')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ cái viết thường')
        
        if not re.search(r'\d', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 chữ số')
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', v):
            raise ValueError('Mật khẩu phải có ít nhất 1 ký tự đặc biệt')
        
        return v


@router.post("/change-password")
def change_password_with_current(
    request: StudentChangePasswordWithEmailRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Đổi mật khẩu sinh viên với mật khẩu hiện tại (không cần OTP)"""
    
    # Xác thực mật khẩu hiện tại
    if not verify_password(request.current_password, current_student.password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    
    # Kiểm tra mật khẩu mới khác mật khẩu cũ
    if verify_password(request.new_password, current_student.password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    
    # Cập nhật mật khẩu với SHA256
    current_student.password = hash_password_sha256(request.new_password)
    current_student.password_updated_at = datetime.now()
    
    try:
        db.commit()
        return {"message": "Đổi mật khẩu thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật mật khẩu")


class StudentProfileRequest(BaseModel):
    student_email: str


@router.post("/profile")
def get_student_profile(
    request: StudentProfileRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Lấy thông tin sinh viên profile"""
    student = db.query(Student).filter(Student.id == current_student.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
    return {
        "student_id": student.student_id,
        "student_name": student.student_name,
        "email": student.email,
        "course_id": student.course_id,
        "password_updated_at": student.password_updated_at
    }