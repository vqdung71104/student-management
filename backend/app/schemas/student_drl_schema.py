from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class StudentDRLBase(BaseModel):
    student_id: str
    semester: str
    drl_score: int

    @validator('semester')
    def validate_semester(cls, v):
        # Semester format: YYYYS (VD: 20241, 20242)
        # Chuyển về string để validate
        v_str = str(v)
        if len(v_str) != 5:
            raise ValueError('Semester phải có format YYYYS (VD: 20241)')
        try:
            year = int(v_str[:4])
            sem = int(v_str[4])
            if year < 2020 or year > 2030:
                raise ValueError('Năm phải từ 2020-2030')
            if sem < 1 or sem > 3:
                raise ValueError('Kỳ phải từ 1-3')
        except ValueError:
            raise ValueError('Semester không hợp lệ, phải có format YYYYS')
        return v_str

    @validator('drl_score')
    def validate_drl_score(cls, v):
        if v < -50 or v > 100:
            raise ValueError('Điểm rèn luyện phải từ -50 đến 100')
        return v


class StudentDRLCreate(StudentDRLBase):
    pass


class StudentDRLUpdate(BaseModel):
    semester: Optional[str] = None
    drl_score: Optional[int] = None

    @validator('semester')
    def validate_semester(cls, v):
        if v is not None:
            # Semester format: YYYYS (VD: 20241, 20242)
            v_str = str(v)
            if len(v_str) != 5:
                raise ValueError('Semester phải có format YYYYS (VD: 20241)')
            try:
                year = int(v_str[:4])
                sem = int(v_str[4])
                if year < 2020 or year > 2030:
                    raise ValueError('Năm phải từ 2020-2030')
                if sem < 1 or sem > 3:
                    raise ValueError('Kỳ phải từ 1-3')
            except ValueError:
                raise ValueError('Semester không hợp lệ, phải có format YYYYS')
            return v_str
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