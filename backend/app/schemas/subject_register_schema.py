from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Base model chỉ chứa subject_name và credits (được lấy tự động)
class SubjectRegisterBase(BaseModel):
    subject_name: str
    credits: int

# Khi tạo: chỉ cần student_id và subject_id
class SubjectRegisterCreate(BaseModel):
    student_id: int
    subject_id: int

# Khi update: chỉ cho phép update student_id hoặc subject_id (subject_name, credits tự động)
class SubjectRegisterUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None

# Response: hiển thị đủ trường bao gồm register_date
class SubjectRegisterResponse(SubjectRegisterBase):
    id: int
    student_id: int
    subject_id: int
    register_date: datetime

    class Config:
        from_attributes = True
