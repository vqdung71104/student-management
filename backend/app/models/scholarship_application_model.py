from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
import enum


class FamilyStatus(enum.Enum):
    BINH_THUONG = "bình thường"
    KHO_KHAN = "khó khăn"
    CAN_NGHEO = "cận nghèo"
    NGHEO = "nghèo"


class ApplicationStatus(enum.Enum):
    CHO_DUYET = "Chờ duyệt"
    DA_DUYET = "Đã duyệt"
    BI_TU_CHOI = "Bị từ chối"


class ScholarshipApplication(Base):
    __tablename__ = "scholarship_applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scholarship_id = Column(Integer, ForeignKey('scholarships.id'), nullable=False)
    student_id = Column(String(50), ForeignKey('students.student_id'), nullable=False)
    
    # Thông tin ngân hàng
    bank_account_number = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Thông tin gia đình và địa chỉ
    family_status = Column(Enum(FamilyStatus), nullable=True)
    address_country = Column(String(100), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_ward = Column(String(100), nullable=True)
    address_detail = Column(String(255), nullable=True)
    family_description = Column(Text, nullable=True)
    
    # Thành tích và lý do
    achievement_special = Column(Text, nullable=True)
    achievement_activity = Column(Text, nullable=True)
    reason_apply = Column(Text, nullable=True)
    attachment_url = Column(String(255), nullable=True)
    
    # Thông tin tự động từ CSDL sinh viên
    auto_cpa = Column(Float, nullable=True)
    auto_gpa = Column(Float, nullable=True)
    auto_drl_latest = Column(Integer, nullable=True)
    auto_drl_average = Column(Float, nullable=True)
    auto_gpa_last_2_sem = Column(Float, nullable=True)
    auto_drl_last_2_sem = Column(String(50), nullable=True)  # "85, 90" or json
    auto_total_credits = Column(Integer, nullable=True)
    
    # Trạng thái duyệt
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.CHO_DUYET)
    reviewed_by = Column(String(100), nullable=True)  # admin duyệt
    reviewed_at = Column(DateTime, nullable=True)
    note_admin = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    scholarship = relationship("Scholarship", back_populates="applications")
    student = relationship("Student", back_populates="scholarship_applications")