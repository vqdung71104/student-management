from sqlalchemy import Column, String, Integer, Time, ForeignKey
from sqlalchemy.orm import relationship, validates
from app.db.database import Base
from datetime import datetime, time
from typing import ClassVar, Set
from sqlalchemy.types import JSON


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    class_id = Column(String(255), unique=True)
    class_name = Column(String(255))
    linked_class_ids = Column(String(255))
    class_type = Column(String(255))
    classroom = Column(String(255))
    study_date = Column(String(255))  # ví dụ: "Monday,Tuesday"
    study_time_start = Column(Time)   # 09:05
    study_time_end = Column(Time)     # 10:00
    max_student_number = Column(Integer)
    teacher_name = Column(String(255))
    study_week = Column(JSON)  # số tuần học

    subject = relationship("Subject", back_populates="classes")
    class_registers = relationship("ClassRegister", back_populates="class_info_rel")

    # ---------------- VALIDATOR ----------------
    VALID_DAYS: ClassVar[Set[str]] = {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    }

    @validates("study_date")
    def validate_study_date(self, key, value: str):
        """Đảm bảo study_date chỉ chứa tên ngày hợp lệ, phân tách bằng dấu phẩy"""
        if not value:
            return value
        days = [day.strip() for day in value.split(",")]
        for d in days:
            if d not in self.VALID_DAYS:
                raise ValueError(f"Invalid day '{d}'. Must be one of {', '.join(self.VALID_DAYS)}")
        return ",".join(days)  # chuẩn hóa lại chuỗi

    @validates("study_time_start", "study_time_end")
    def validate_time(self, key, value):
        """Đảm bảo thời gian có format hh:mm và lưu thành datetime.time"""
        if isinstance(value, str):
            try:
                parsed = datetime.strptime(value, "%H:%M").time()
                return parsed
            except ValueError:
                raise ValueError(f"{key} must be in format HH:MM (e.g. 09:05)")
        elif isinstance(value, time):
            return value
        else:
            raise ValueError(f"{key} must be a string 'HH:MM' or datetime.time instance")
