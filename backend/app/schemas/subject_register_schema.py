from typing import List, Optional
from pydantic import BaseModel
from app.schemas.subject_schema import SubjectResponse
from app.schemas.student_schemas import StudentResponse
class SubjectRegisterBase(BaseModel):
    subject_name: str
    credits: int
    conditional_subject: List[str] = []

class SubjectRegisterCreate(SubjectRegisterBase):
    student_id: str
    subject_id: str

class SubjectRegisterUpdate(BaseModel):
    subject_name: Optional[str] = None
    credits: Optional[int] = None
    conditional_subject: Optional[List[str]] = None

class SubjectRegisterResponse(SubjectRegisterBase):
    student: StudentResponse
    subject: SubjectResponse

    class Config:
        from_attributes = True
