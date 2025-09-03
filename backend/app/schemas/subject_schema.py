from typing import List, Optional
from pydantic import BaseModel
from app.schemas.department_schema import DepartmentResponse


class SubjectBase(BaseModel):
    subject_id: str
    subject_name: str
    duration: int
    credits: int
    tuition_fee: float
    english_subject_name: str
    weight: float
    conditional_subject: List[str] = []  # ID các môn học điều kiện

class SubjectCreate(SubjectBase):
    department_id: str

class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = None
    duration: Optional[int] = None
    credits: Optional[int] = None
    tuition_fee: Optional[float] = None
    english_subject_name: Optional[str] = None
    weight: Optional[float] = None
    conditional_subject: Optional[List[str]] = None
    department_id: Optional[str] = None

class SubjectResponse(SubjectBase):
    department: DepartmentResponse

    class Config:
        from_attributes = True
