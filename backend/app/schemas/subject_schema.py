from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.department_schema import DepartmentResponse

class SubjectBase(BaseModel):
    subject_id: str = Field(..., max_length=50)
    subject_name: str = Field(..., max_length=255)
    duration: str = Field(..., max_length=50)
    credits: int
    tuition_fee: int
    english_subject_name: str = Field(..., max_length=255)
    weight: float
    conditional_subjects: Optional[str] = None  # Changed to str to match DB

class SubjectCreate(SubjectBase):
    department_id: str = Field(..., max_length=50)

class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, max_length=255)
    duration: Optional[str] = None
    credits: Optional[int] = None
    tuition_fee: Optional[int] = None
    english_subject_name: Optional[str] = Field(None, max_length=255)
    weight: Optional[float] = None
    conditional_subjects: Optional[str] = None  # Changed to str
    department_id: Optional[str] = Field(None, max_length=50)

class SubjectResponse(SubjectBase):
    id: int
    department: DepartmentResponse

    class Config:
        from_attributes = True