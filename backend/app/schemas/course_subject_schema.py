from typing import Optional
from pydantic import BaseModel

class CourseSubjectBase(BaseModel):
    subject_name: str

class CourseSubjectCreate(CourseSubjectBase):
    subject_id: str
    course_id: str

class CourseSubjectUpdate(BaseModel):
    subject_name: Optional[str] = None

class CourseSubjectResponse(CourseSubjectBase):
    id: str
    subject_id: str
    course_id: str

    class Config:
        from_attributes = True
