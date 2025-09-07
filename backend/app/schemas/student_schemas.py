from pydantic import BaseModel, validator, EmailStr
from typing import Optional
import re
import unicodedata


class StudentBase(BaseModel):
    """Base fields that can be manually set"""
    student_name: str
    enrolled_year: int
    student_id: str
    course_id: int    
    training_level: str
    learning_status: str
    gender: str
    classes: Optional[str] = None
    newest_semester: Optional[str] = None
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
        allowed = ["Đang học", "Bảo lưu", "Thôi học", "Buộc thôi học"]
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
    
    def remove_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    def generate_email(self) -> str:
        """Tạo email từ tên + MSSV"""
        unaccented_name = self.remove_accents(self.student_name.strip())
        name_parts = unaccented_name.split()
        last_name = name_parts[-1].lower()
        initials = "".join([w[0].lower() for w in name_parts[:-1]])
        mssv_suffix = self.student_id[2:]  # bỏ 2 số đầu
        return f"{last_name}.{initials}{mssv_suffix}@sis.hust.edu.vn"


class StudentCreate(StudentBase):
    """Schema for creating students - no auto-calculated fields"""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating students - only manually editable fields"""
    student_name: Optional[str] = None
    enrolled_year: Optional[int] = None
    training_level: Optional[str] = None
    learning_status: Optional[str] = None
    gender: Optional[str] = None
    classes: Optional[str] = None
    newest_semester: Optional[str] = None
    department_id: Optional[str] = None
    course_id: Optional[int] = None

    @validator("training_level")
    def validate_training_level(cls, v):
        if v is not None:
            allowed = ["Cử nhân", "Kỹ sư", "Thạc sỹ", "Tiến sỹ"]
            if v not in allowed:
                raise ValueError(f"training_level chỉ được chọn {allowed}")
        return v

    @validator("learning_status")
    def validate_learning_status(cls, v):
        if v is not None:
            allowed = ["Đang học", "Bảo lưu", "Thôi học", "Buộc thôi học"]
            if v not in allowed:
                raise ValueError(f"learning_status chỉ được chọn {allowed}")
        return v

    @validator("gender")
    def validate_gender(cls, v):
        if v is not None:
            allowed = ["Nam", "Nữ"]
            if v not in allowed:
                raise ValueError(f"gender chỉ được chọn {allowed}")
        return v

    @validator("student_name")
    def strip_spaces(cls, v):
        if v is not None:
            return " ".join(v.split())
        return v


class StudentResponse(StudentBase):
    """Schema for response - includes all fields including auto-calculated ones"""
    id: int
    email: EmailStr
    
    # Auto-calculated fields - shown in response but not editable
    cpa: float = 0.0
    failed_subjects_number: int = 0
    study_subjects_number: int = 0
    total_failed_credits: int = 0
    total_learned_credits: int = 0
    year_level: str = "Trình độ năm 1"
    warning_level: str = "Cảnh cáo mức 0"
    level_3_warning_number: int = 0

    class Config:
        from_attributes = True
