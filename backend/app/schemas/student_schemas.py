from pydantic import BaseModel, validator, EmailStr
from typing import Optional
import re


class StudentBase(BaseModel):
    student_id: str
    student_name: str
    course_id: str
    enrolled_year: int
    training_level: str
    learning_status: str
    gender: str
    classes: Optional[str] = None
    newest_semester: Optional[str] = None
    cpa: Optional[float] = 0.0
    failed_subjects_number: Optional[int] = 0
    study_subjects_number: Optional[int] = 0
    year_level: Optional[str] = None
    warning_level: Optional[str] = None
    level_3_warning_number: Optional[int] = 0
    department_id: Optional[str] = None

    @validator("student_id")
    def validate_student_id(cls, v, values):
        enrolled_year = values.get("enrolled_year")
        if not v.startswith(str(enrolled_year)):
            raise ValueError(f"student_id phải bắt đầu bằng năm nhập học {enrolled_year}")
        return v

    @validator("training_level")
    def validate_training_level(cls, v):
        allowed = ["Cử nhân", "Kỹ sư", "Thạc sỹ", "Tiến sỹ"]
        if v not in allowed:
            raise ValueError(f"training_level chỉ được chọn {allowed}")
        return v

    @validator("learning_status")
    def validate_learning_status(cls, v):
        allowed = ["Đang học", "Thôi học", "Buộc thôi học"]
        if v not in allowed:
            raise ValueError(f"learning_status chỉ được chọn {allowed}")
        return v

    @validator("gender")
    def validate_gender(cls, v):
        allowed = ["Nam", "Nữ"]
        if v not in allowed:
            raise ValueError(f"gender chỉ được chọn {allowed}")
        return v

    @validator("student_name")
    def strip_spaces(cls, v):
        return " ".join(v.split())

    def generate_email(self) -> str:
        """Tạo email từ tên + MSSV"""
        name_parts = self.student_name.strip().split()
        last_name = name_parts[-1].lower()
        initials = "".join([w[0].lower() for w in name_parts[:-1]])
        mssv_suffix = self.student_id[2:]  # bỏ 2 số đầu
        return f"{last_name}.{initials}{mssv_suffix}@sis.hust.edu.vn"


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    student_id: Optional[str] = None
    enrolled_year: Optional[int] = None
    training_level: Optional[str] = None
    learning_status: Optional[str] = None
    gender: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True
