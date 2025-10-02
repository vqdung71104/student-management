from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.enums import ProjectType, ProjectStatus


class StudentProjectsBase(BaseModel):
    student_id: str
    subject_id: str
    type: ProjectType
    teacher_name: str
    topic: str
    scores: Optional[int] = None
    status: ProjectStatus = ProjectStatus.PENDING

    @validator('scores')
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Điểm phải từ 0-100')
        return v


class StudentProjectsCreate(StudentProjectsBase):
    pass


class StudentProjectsUpdate(BaseModel):
    subject_id: Optional[str] = None
    type: Optional[ProjectType] = None
    teacher_name: Optional[str] = None
    topic: Optional[str] = None
    scores: Optional[int] = None
    status: Optional[ProjectStatus] = None

    @validator('scores')
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Điểm phải từ 0-100')
        return v


class StudentProjectsResponse(StudentProjectsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True