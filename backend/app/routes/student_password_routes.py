from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.student_model import Student
from app.schemas.student_schemas import (
    StudentChangePasswordRequest, 
    StudentRequestPasswordResetRequest, 
    StudentVerifyOTPRequest,
    StudentPasswordResetResponse
)
from app.services.email_service import email_service
import hashlib
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
    db: Session = Depends(get_db)
):
    """Yêu cầu đổi mật khẩu sinh viên - gửi OTP qua email"""
    # Kiểm tra sinh viên có tồn tại không
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Email sinh viên không tồn tại")
    
    # Tạo và gửi OTP
    otp = email_service.create_otp_record(db, request.email, "student_password_reset")
    if not otp:
        raise HTTPException(status_code=500, detail="Không thể tạo mã OTP")
    
    # Gửi email
    if not email_service.send_otp_email(request.email, otp, "student_password_reset"):
        raise HTTPException(status_code=500, detail="Không thể gửi email OTP")
    
    return StudentPasswordResetResponse(
        message="Mã OTP đã được gửi đến email của bạn",
        expires_in=600  # 10 phút
    )


@router.post("/verify-otp-and-change-password")
def verify_otp_and_change_password(
    request: StudentVerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Xác thực OTP và đổi mật khẩu sinh viên"""
    # Kiểm tra sinh viên có tồn tại không
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Email sinh viên không tồn tại")
    
    # Xác thực OTP
    if not email_service.verify_otp(db, request.email, request.otp, "student_password_reset"):
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ hoặc đã hết hạn")
    
    # Kiểm tra mật khẩu mới khác mật khẩu cũ
    new_password_hash = hash_password_sha256(request.new_password)
    if verify_password(request.new_password, student.login_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    
    # Cập nhật mật khẩu với SHA256
    student.login_password = new_password_hash
    student.password_updated_at = datetime.now()
    
    try:
        db.commit()
        return {"message": "Đổi mật khẩu thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật mật khẩu")


@router.post("/change-password")
def change_password_with_current(
    request: StudentChangePasswordRequest,
    student_email: str,  # Từ session/token
    db: Session = Depends(get_db)
):
    """Đổi mật khẩu sinh viên với mật khẩu hiện tại (không cần OTP)"""
    # Lấy thông tin sinh viên
    student = db.query(Student).filter(Student.email == student_email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
    
    # Xác thực mật khẩu hiện tại
    if not verify_password(request.current_password, student.login_password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    
    # Kiểm tra mật khẩu mới khác mật khẩu cũ
    if verify_password(request.new_password, student.login_password):
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    
    # Cập nhật mật khẩu với SHA256
    student.login_password = hash_password_sha256(request.new_password)
    student.password_updated_at = datetime.now()
    
    try:
        db.commit()
        return {"message": "Đổi mật khẩu thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật mật khẩu")


@router.get("/profile")
def get_student_profile(student_email: str, db: Session = Depends(get_db)):
    """Lấy thông tin sinh viên profile"""
    student = db.query(Student).filter(Student.email == student_email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
    
    return {
        "student_id": student.student_id,
        "student_name": student.student_name,
        "email": student.email,
        "course_id": student.course_id,
        "classes": student.classes,
        "password_updated_at": student.password_updated_at
    }