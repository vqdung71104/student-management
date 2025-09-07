from typing import Optional
from pydantic import BaseModel

class SemesterGPABase(BaseModel):
    semester: str  # 20231
    gpa: float

class SemesterGPACreate(SemesterGPABase):
    student_id: int

class SemesterGPAUpdate(BaseModel):
    semester: Optional[str] = None
    gpa: Optional[float] = None

class SemesterGPAResponse(SemesterGPABase):
    id: int
    student_id: int

    class Config:
        from_attributes = True
