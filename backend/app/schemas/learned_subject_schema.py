from typing import Optional
from pydantic import BaseModel

class LearnedSubjectBase(BaseModel):
    subject_name: str
    credits: int
    final_score: float
    midterm_score: float
    weight: float
    total_score: float
    letter_grade: str
    semester: str

class LearnedSubjectCreate(LearnedSubjectBase):
    student_id: int
    subject_id: str

class LearnedSubjectUpdate(BaseModel):
    subject_name: Optional[str] = None
    credits: Optional[int] = None
    final_score: Optional[float] = None
    midterm_score: Optional[float] = None
    weight: Optional[float] = None
    total_score: Optional[float] = None
    letter_grade: Optional[str] = None
    semester: Optional[str] = None

class LearnedSubjectResponse(LearnedSubjectBase):
    id: int
    student_id: int
    subject_id: str

    class Config:
        from_attributes = True
