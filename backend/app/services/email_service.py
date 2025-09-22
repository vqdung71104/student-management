import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.otp_model import OTPVerification
from typing import Optional
import os


class EmailService:
    def __init__(self):
        # Cấu hình SMTP - có thể chuyển vào environment variables
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "vuquangdung71104@gmail.com"
        self.sender_password = os.getenv("EMAIL_PASSWORD", "your_app_password_here")  # App password
        
    def generate_otp(self) -> str:
        """Tạo mã OTP 6 chữ số"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_otp_email(self, recipient_email: str, otp: str, purpose: str = "password_reset") -> bool:
        """Gửi email chứa mã OTP"""
        try:
            # Tạo nội dung email
            message = MIMEMultipart("alternative")
            
            if purpose == "student_password_reset":
                message["Subject"] = "Mã xác thực đổi mật khẩu sinh viên - Student Management System"
                title = "Yêu cầu đổi mật khẩu sinh viên"
                description = "Chúng tôi đã nhận được yêu cầu đổi mật khẩu cho tài khoản sinh viên của bạn."
            else:
                message["Subject"] = "Mã xác thực đổi mật khẩu - Student Management System"
                title = "Yêu cầu đổi mật khẩu"
                description = "Chúng tôi đã nhận được yêu cầu đổi mật khẩu cho tài khoản admin của bạn."
            
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Nội dung email HTML
            html_content = f"""
            <html>
              <body>
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
                  <h2 style="color: #2563eb; text-align: center;">Student Management System</h2>
                  <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-bottom: 16px;">{title}</h3>
                    <p style="color: #4b5563; line-height: 1.6;">
                      {description}
                    </p>
                    <div style="background-color: #2563eb; color: white; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0;">
                      <h2 style="margin: 0; font-size: 24px; letter-spacing: 3px;">{otp}</h2>
                    </div>
                    <p style="color: #4b5563; line-height: 1.6;">
                      Mã xác thực này có hiệu lực trong <strong>10 phút</strong>.
                      Vui lòng không chia sẻ mã này với bất kỳ ai.
                    </p>
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #6b7280; font-size: 14px;">
                      Nếu bạn không yêu cầu đổi mật khẩu, vui lòng bỏ qua email này.
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Nội dung email text thuần
            text_content = f"""
            Student Management System
            
            {title}
            
            {description}
            
            Mã xác thực của bạn là: {otp}
            
            Mã xác thực này có hiệu lực trong 10 phút.
            Vui lòng không chia sẻ mã này với bất kỳ ai.
            
            Nếu bạn không yêu cầu đổi mật khẩu, vui lòng bỏ qua email này.
            """
            
            # Thêm nội dung vào email
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Gửi email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
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
                expires_at=datetime.now() + timedelta(minutes=10)  # 10 phút
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