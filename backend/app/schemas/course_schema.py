from typing import List, Optional
from pydantic import BaseModel

class CourseSubjectSchema(BaseModel):
    subject_id: str
    subject_name: str

class CourseBase(BaseModel):
    course_id: str
    course_name: str

class CourseCreate(CourseBase):
    subjects: List[CourseSubjectSchema] = []

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    subjects: Optional[List[CourseSubjectSchema]] = None

class CourseResponse(CourseBase):
    subjects: List[CourseSubjectSchema]

    class Config:
        from_attributes = True
