import random
import string
import smtplib
import importlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings


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

    def send_reset_password_email(self, recipient_email: str, reset_url: str) -> bool:
        """Send reset-password link using Gmail SMTP."""
        try:
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
                print("SMTP credentials are missing. Skipping email send.")
                return False

            subject = "Reset mật khẩu - Student Management"
            html_body = f"""
            <html>
              <body>
                <p>Xin chào,</p>
                <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
                <p>Nhấn vào liên kết bên dưới để đặt lại mật khẩu (hiệu lực trong thời gian ngắn):</p>
                <p><a href=\"{reset_url}\">Đặt lại mật khẩu</a></p>
                <p>Nếu bạn không yêu cầu, hãy bỏ qua email này.</p>
              </body>
            </html>
            """

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_SENDER
            message["To"] = recipient_email
            message.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_SENDER, recipient_email, message.as_string())

            return True
        except Exception as e:
            print(f"Lỗi gửi email reset password: {str(e)}")
            return False
    
    def create_otp_record(self, db: Session, email: str, purpose: str = "password_reset") -> Optional[str]:
        """Tạo và lưu mã OTP vào database"""
        try:
            otp_module = importlib.import_module("app.models.otp_verification_model")
            OTPVerification = getattr(otp_module, "OTPVerification", None)
            if OTPVerification is None:
                return None

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
            otp_module = importlib.import_module("app.models.otp_verification_model")
            OTPVerification = getattr(otp_module, "OTPVerification", None)
            if OTPVerification is None:
                return False

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