import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.otp_model import OTPVerification
from typing import Optional


class EmailService:
    def __init__(self):
        pass
        
    def generate_otp(self) -> str:
        """Tạo mã OTP 6 chữ số"""
        return "".join(random.choices(string.digits, k=6))
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "password_reset") -> bool:
        """Gửi email chứa mã OTP - MOCK VERSION"""
        try:
            print("\n======================")
            print("MOCK EMAIL SENT")
            print(f"To: {recipient_email}")
            if purpose == "student_password_reset":
                print("Subject: Mã xác thực đổi mật khẩu sinh viên")
            else:
                print("Subject: Mã xác thực đổi mật khẩu admin")
            print(f"Purpose: {purpose}")
            print(f"OTP Code: {otp}")
            print(f"Valid for: 10 minutes")
            print("======================\n")
            return True
        except Exception as e:
            print(f"Lỗi gửi email: {str(e)}")
            return False
    
    def create_otp_record(self, db: Session, email: str, purpose: str = "password_reset") -> Optional[str]:
        """Tạo và lưu mã OTP vào database"""
        try:
            # Xóa các OTP cũ chưa sử dụng của email này
            db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.is_used == "no"
            ).delete()
            
            # Tạo OTP mới
            otp = self.generate_otp()
            otp_record = OTPVerification(
                email=email,
                otp_code=otp,
                purpose=purpose,
                expires_at=datetime.now() + timedelta(minutes=10)
            )
            
            db.add(otp_record)
            db.commit()
            return otp
        except Exception as e:
            print(f"Lỗi tạo OTP record: {str(e)}")
            db.rollback()
            return None
    
    def verify_otp(self, db: Session, email: str, otp: str, purpose: str = "password_reset") -> bool:
        """Xác thực mã OTP"""
        try:
            otp_record = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.otp_code == otp,
                OTPVerification.purpose == purpose,
                OTPVerification.is_used == "no",
                OTPVerification.expires_at > datetime.now()
            ).first()
            
            if otp_record:
                # Đánh dấu OTP đã sử dụng
                otp_record.is_used = "yes"
                db.commit()
                return True
            return False
        except Exception as e:
            print(f"Lỗi xác thực OTP: {str(e)}")
            return False


# Khởi tạo service
email_service = EmailService()