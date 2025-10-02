from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class StudentDRLBase(BaseModel):
    student_id: str
    semester: int
    drl_score: int

    @validator('semester')
    def validate_semester(cls, v):
        if v < 1 or v > 14:
            raise ValueError('Semester phải từ 1-14')
        return v

    @validator('drl_score')
    def validate_drl_score(cls, v):
        if v < -50 or v > 100:
            raise ValueError('Điểm rèn luyện phải từ -50 đến 100')
        return v


class StudentDRLCreate(StudentDRLBase):
    pass


class StudentDRLUpdate(BaseModel):
    semester: Optional[int] = None
    drl_score: Optional[int] = None

    @validator('semester')
    def validate_semester(cls, v):
        if v is not None and (v < 1 or v > 14):
            raise ValueError('Semester phải từ 1-14')
        return v

    @validator('drl_score')
    def validate_drl_score(cls, v):
        if v is not None and (v < -50 or v > 100):
            raise ValueError('Điểm rèn luyện phải từ -50 đến 100')
        return v


class StudentDRLResponse(StudentDRLBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True