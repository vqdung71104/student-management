from typing import List, Optional
from pydantic import BaseModel
from app.schemas.enums import TrainingLevel, LearningStatus, Gender, YearLevel, WarningLevel
from app.schemas.course_schema import CourseResponse
from app.schemas.department_schema import DepartmentResponse

class LearnedSubjectSchema(BaseModel):
    subject_id: str
    subject_name: str
    credits: int
    final_score: float
    midterm_score: float
    weight: float
    total_score: float
    letter_grade: str
    semester: str

class SemesterGPASchema(BaseModel):
    semester: str
    gpa: float

class StudentBase(BaseModel):
    student_name: str
    student_id: str
    enrolled_year: int
    training_level: TrainingLevel
    learning_status: LearningStatus
    gender: Gender
    classes: str
    intake: int
    email: str
    newest_semester: str
    cpa: float
    failed_courses_number: int
    courses_number: int
    year_level: YearLevel
    warning_level: WarningLevel
    level_3_warning_number: int

class StudentCreate(StudentBase):
    enrolled_courses: List[str] = []  # course_id list
    department_id: str
    learned_subjects: List[LearnedSubjectSchema] = []
    semester_gpa: List[SemesterGPASchema] = []

class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    enrolled_year: Optional[int] = None
    training_level: Optional[TrainingLevel] = None
    learning_status: Optional[LearningStatus] = None
    gender: Optional[Gender] = None
    classes: Optional[str] = None
    intake: Optional[int] = None
    email: Optional[str] = None
    newest_semester: Optional[str] = None
    cpa: Optional[float] = None
    failed_courses_number: Optional[int] = None
    courses_number: Optional[int] = None
    year_level: Optional[YearLevel] = None
    warning_level: Optional[WarningLevel] = None
    level_3_warning_number: Optional[int] = None
    enrolled_courses: Optional[List[str]] = None
    department_id: Optional[str] = None
    learned_subjects: Optional[List[LearnedSubjectSchema]] = None
    semester_gpa: Optional[List[SemesterGPASchema]] = None

class StudentResponse(StudentBase):
    enrolled_courses: List[CourseResponse]
    department: DepartmentResponse
    learned_subjects: List[LearnedSubjectSchema]
    semester_gpa: List[SemesterGPASchema]

    class Config:
        from_attributes = True
