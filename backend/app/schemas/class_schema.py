from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.subject_schema import SubjectResponse
from app.schemas.enums import ClassType

class ClassBase(BaseModel):
    class_id: str
    class_name: str
    linked_class_ids: List[str] = []
    class_type: ClassType
    classroom: str
    study_date: str
    study_time: datetime
    max_student_number: int
    teacher_name: str
    study_week: str

class ClassCreate(ClassBase):
    subject_id: str

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    linked_class_ids: Optional[List[str]] = None
    class_type: Optional[ClassType] = None
    classroom: Optional[str] = None
    study_date: Optional[str] = None
    study_time: Optional[datetime] = None
    max_student_number: Optional[int] = None
    teacher_name: Optional[str] = None
    study_week: Optional[str] = None
    subject_id: Optional[str] = None

class ClassResponse(ClassBase):
    subject: SubjectResponse

    class Config:
        from_attributes = True
