from typing import Optional
from pydantic import BaseModel

class CourseSubjectBase(BaseModel):
    pass

class CourseSubjectCreate(CourseSubjectBase):
    subject_id: int  # Integer ID từ database
    course_id: int

class CourseSubjectUpdate(BaseModel):
    subject_id: Optional[int] = None
    course_id: Optional[int] = None

class CourseSubjectResponse(CourseSubjectBase):
    id: int
    course_id: int
    subject_id: int
    
   

    class Config:
        from_attributes = True
