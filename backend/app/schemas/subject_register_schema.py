from typing import List, Optional
from pydantic import BaseModel

class SubjectRegisterBase(BaseModel):
    subject_name: str
    credits: int

class SubjectRegisterCreate(SubjectRegisterBase):
    student_id: int
    subject_id: str

class SubjectRegisterUpdate(BaseModel):
    subject_name: Optional[str] = None
    credits: Optional[int] = None

class SubjectRegisterResponse(SubjectRegisterBase):
    id: int
    student_id: int
    subject_id: str

    class Config:
        from_attributes = True
