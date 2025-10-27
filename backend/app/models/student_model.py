from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.associations import student_course_table


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"))
    password_updated_at = Column(DateTime, default=func.now(), nullable=True)  # Thời gian đổi mật khẩu gần nhất
    cpa = Column(Float, default=0.0)
    failed_subjects_number = Column(Integer, default=0)
    study_subjects_number = Column(Integer, default=0)
    total_learned_credits = Column(Integer, default=0)
    total_failed_credits = Column(Integer, default=0)
    year_level = Column(String(20), default="Trình độ năm 1")  #enum-like
    warning_level = Column(String(50), default="Cảnh cáo mức 0")  #enum-like
    level_3_warning_number = Column(Integer, default=0)

    # Relationships
    department = relationship("Department", back_populates="students")
    learned_subjects = relationship("LearnedSubject", back_populates="student")
    semester_gpa = relationship("SemesterGPA", back_populates="student")
    class_registers = relationship("ClassRegister", back_populates="student")
    subject_registers = relationship("SubjectRegister", back_populates="student")
    enrolled_courses = relationship(
        "Course", secondary=student_course_table, back_populates="enrolled_students"
    )

