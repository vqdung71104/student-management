from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.admin_model import Admin
from app.schemas.admin_schema import (
    ChangePasswordRequest, 
    RequestPasswordResetRequest, 
    VerifyOTPRequest,
    PasswordResetResponse,
    AdminResponse
)
from app.services.email_service import email_service
import hashlib
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin Password Management"])


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed_password


def check_password_expiry(admin: Admin) -> bool:
    """Kiểm tra xem mật khẩu có hết hạn không (3 tháng)"""
    if not admin.password_updated_at:
        return True  # Chưa có thông tin, cần đổi mật khẩu
    
    expiry_date = admin.password_updated_at + timedelta(days=90)  # 3 tháng
    return datetime.now() > expiry_date


@router.get("/profile", response_model=AdminResponse)
def get_admin_profile(admin_username: str = "admin", db: Session = Depends(get_db)):
    """Lấy thông tin admin profile"""
    admin = db.query(Admin).filter(Admin.username == admin_username).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin không tồn tại")
    
    return admin


@router.post("/request-password-reset", response_model=PasswordResetResponse)
def request_password_reset(
    request: RequestPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Yêu cầu đổi mật khẩu - gửi OTP qua email"""
    # Kiểm tra admin có tồn tại không
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Email admin không tồn tại")
    
    # Tạo và gửi OTP
    otp = email_service.create_otp_record(db, request.email, "password_reset")
    if not otp:
        raise HTTPException(status_code=500, detail="Không thể tạo mã OTP")
    
    # Gửi email
    if not email_service.send_otp_email(request.email, otp, "password_reset"):
        raise HTTPException(status_code=500, detail="Không thể gửi email OTP")
    
    return PasswordResetResponse(
        message="Mã OTP đã được gửi đến email của bạn",
        expires_in=600  # 10 phút
    )


@router.post("/verify-otp-and-change-password")
def verify_otp_and_change_password(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Xác thực OTP và đổi mật khẩu"""
    # Kiểm tra admin có tồn tại không
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Email admin không tồn tại")
    
    # Xác thực OTP
    if not email_service.verify_otp(db, request.email, request.otp, "password_reset"):
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ hoặc đã hết hạn")
    
    # Kiểm tra mật khẩu mới khác mật khẩu cũ
    new_password_hash = hash_password(request.new_password)
    if admin.password_hash == new_password_hash:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    
    # Cập nhật mật khẩu
    admin.password_hash = new_password_hash
    admin.password_updated_at = datetime.now()
    
    try:
        db.commit()
        return {"message": "Đổi mật khẩu thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật mật khẩu")


@router.post("/change-password")
def change_password_with_current(
    request: ChangePasswordRequest,
    admin_username: str = "admin",  # Từ session/token
    db: Session = Depends(get_db)
):
    """Đổi mật khẩu với mật khẩu hiện tại (không cần OTP)"""
    # Lấy thông tin admin
    admin = db.query(Admin).filter(Admin.username == admin_username).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin không tồn tại")
    
    # Xác thực mật khẩu hiện tại
    if not verify_password(request.current_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    
    # Kiểm tra mật khẩu mới khác mật khẩu cũ
    new_password_hash = hash_password(request.new_password)
    if admin.password_hash == new_password_hash:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")
    
    # Cập nhật mật khẩu
    admin.password_hash = new_password_hash
    admin.password_updated_at = datetime.now()
    
    try:
        db.commit()
        return {"message": "Đổi mật khẩu thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật mật khẩu")


@router.get("/password-status")
def check_password_status(admin_username: str = "admin", db: Session = Depends(get_db)):
    """Kiểm tra trạng thái mật khẩu (có hết hạn không)"""
    admin = db.query(Admin).filter(Admin.username == admin_username).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin không tồn tại")
    
    is_expired = check_password_expiry(admin)
    days_until_expiry = None
    
    if not is_expired and admin.password_updated_at:
        expiry_date = admin.password_updated_at + timedelta(days=90)
        days_until_expiry = (expiry_date - datetime.now()).days
    
    return {
        "is_expired": is_expired,
        "days_until_expiry": days_until_expiry,
        "last_updated": admin.password_updated_at,
        "message": "Mật khẩu đã hết hạn, vui lòng đổi mật khẩu" if is_expired else "Mật khẩu còn hiệu lực"
    }