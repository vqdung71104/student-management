from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import time, datetime
from typing import List
from sqlalchemy import Column, String, Integer, Time, ForeignKey


class ClassBase(BaseModel):
    id: str
    class_name: str
    subject_id: str = None
    linked_class_ids: Optional[list[str]] = None
    class_type: Optional[str] = None
    classroom: Optional[str] = None
    study_date: Optional[str] = None  # ví dụ: "Monday,Tuesday"
    study_time_start: Optional[time] = None
    study_time_end: Optional[time] = None
    max_student_number: Optional[int] = None
    teacher_name: Optional[str] = None
    study_week: List[int]  # số tuần học

    # -------- VALIDATORS --------
    @field_validator("study_date")
    @classmethod
    def validate_study_date(cls, value: Optional[str]):
        """Đảm bảo study_date chỉ chứa ngày hợp lệ (Monday..Sunday)"""
        if not value:
            return value

        valid_days = {
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        }
        days = [d.strip() for d in value.split(",")]

        for d in days:
            if d not in valid_days:
                raise ValueError(f"Invalid day '{d}'. Must be one of {', '.join(valid_days)}")

        return ",".join(days)  # chuẩn hóa chuỗi

    @field_validator("study_time_start", "study_time_end", mode="before")
    @classmethod
    def validate_time(cls, value):
        """Đảm bảo giờ đúng định dạng HH:MM"""
        if value is None:
            return value
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%H:%M").time()
            except ValueError:
                raise ValueError("Time must be in format HH:MM (e.g. 09:05)")
        raise ValueError("Invalid type for time field")

    @field_validator("study_week", mode="before")
    @classmethod
    def validate_study_week(cls, value):
        """Convert comma-separated string to list of integers"""
        if isinstance(value, str) and value:
            try:
                return [int(x.strip()) for x in value.split(",") if x.strip()]
            except ValueError:
                raise ValueError("Invalid study_week format")
        if isinstance(value, list):
            return value
        return []

    @field_validator("linked_class_ids", mode="before")
    @classmethod
    def validate_linked_class_ids(cls, value):
        """Convert comma-separated string to list"""
        if isinstance(value, str) and value:
            return [x.strip() for x in value.split(",") if x.strip()]
        if isinstance(value, list):
            return value
        return []


class ClassCreate(ClassBase):
    pass


class ClassUpdate(ClassBase):
    pass


class ClassResponse(ClassBase):
    id: str
    subject_id: Optional[str]

    model_config = {
        "from_attributes": True  # tương đương orm_mode=True ở Pydantic v1
    }
