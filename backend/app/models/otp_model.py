from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    otp_code = Column(String(6), nullable=False)  # 6-digit OTP
    purpose = Column(String(50), nullable=False)  # password_reset, etc.
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(String(10), default="no", nullable=False)  # yes/no
    
    def __repr__(self):
        return f"<OTPVerification(email='{self.email}', purpose='{self.purpose}', is_used='{self.is_used}')>"