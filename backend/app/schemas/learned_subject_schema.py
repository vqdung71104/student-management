from typing import Optional
from pydantic import BaseModel


class LearnedSubjectBase(BaseModel):
    final_score: float
    midterm_score: float
    weight: float
    semester: str


class LearnedSubjectCreate(LearnedSubjectBase):
    student_id: int
    subject_id: int   # nên để int vì model ForeignKey là Integer


class LearnedSubjectUpdate(BaseModel):
    final_score: Optional[float] = None
    midterm_score: Optional[float] = None
    weight: Optional[float] = None
    semester: Optional[str] = None


class LearnedSubjectResponse(BaseModel):
    id: int
    subject_name: str
    credits: int
    final_score: float
    midterm_score: float
    weight: float
    total_score: float
    letter_grade: str
    semester: str
    student_id: int
    subject_id: int

    class Config:
        from_attributes = True
