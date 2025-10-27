from typing import Optional
from pydantic import BaseModel, Field


class LearnedSubjectBase(BaseModel):
    semester: str
    letter_grade: str


class LearnedSubjectCreate(LearnedSubjectBase):
    student_id: int
    subject_id: int   # nên để int vì model ForeignKey là Integer


class LearnedSubjectSimpleCreate(BaseModel):
    """Schema đơn giản để sinh viên tự thêm học phần"""
    student_id: int  # ID của sinh viên trong bảng students (students.id)
    subject_id: str  # Mã HP dạng string như "IT3080", "PE3305" (Subject.subject_id)
    semester: str 
    letter_grade: str 


class LearnedSubjectUpdate(BaseModel):
    semester: Optional[str] = None
    letter_grade: Optional[str] = None


class LearnedSubjectResponse(BaseModel):
    id: int
    subject_name: str
    credits: int
    letter_grade: str
    semester: str
    student_id: int
    subject_id: int

    class Config:
        from_attributes = True
