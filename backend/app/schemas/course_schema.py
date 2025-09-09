from typing import List, Optional
from pydantic import BaseModel

# Schema cho input/output đều dùng subject_id (string)
class CourseSubjectSchema(BaseModel):
    subject_id: str
    learning_semester: int

class CourseBase(BaseModel):
    course_id: str
    course_name: str

class CourseCreate(CourseBase):
    subjects: List[CourseSubjectSchema] = []

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    subjects: Optional[List[CourseSubjectSchema]] = None

class CourseResponse(CourseBase):
    id: int
    course_subjects: List[CourseSubjectSchema]

    class Config:
        from_attributes = True