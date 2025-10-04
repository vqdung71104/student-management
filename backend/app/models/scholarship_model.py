from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
import enum


class ScholarshipType(enum.Enum):
    DOANH_NGHIEP = "Học bổng Doanh nghiệp"
    NHA_TRUONG = "Học bổng Nhà trường"
    CHINH_PHU = "Học bổng Chính phủ"
    QUOC_TE = "Học bổng Quốc tế"


class Scholarship(Base):
    __tablename__ = "scholarships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # Học bổng Doanh nghiệp / Nhà trường...
    slots = Column(Integer, nullable=False)  # Số lượng học bổng
    value_per_slot = Column(Integer, nullable=False)  # Giá trị mỗi suất
    sponsor = Column(String(255), nullable=True)  # Đối tác cấp học bổng
    register_start_at = Column(DateTime, nullable=False)
    register_end_at = Column(DateTime, nullable=False)
    target_departments = Column(Text, nullable=True)  # danh sách đơn vị (string hoặc JSON)
    target_courses = Column(Text, nullable=True)  # 2022, 2023, 2024...
    target_programs = Column(Text, nullable=True)  # Cử nhân kỹ thuật, tiên tiến...
    contact_person = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    document_url = Column(String(255), nullable=True)  # file tài liệu upload
    description = Column(Text, nullable=True)  # Thông tin chi tiết
    note = Column(Text, nullable=True)  # ghi chú
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    applications = relationship("ScholarshipApplication", back_populates="scholarship")