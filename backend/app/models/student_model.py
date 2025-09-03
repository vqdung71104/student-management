from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    student_id = Column(String, unique=True)
    student_name = Column(String)
    enrolled_year = Column(Integer)
    training_level = Column(String)
    learning_status = Column(String)
    gender = Column(String)
    classes = Column(String)
    intake = Column(Integer)
    email = Column(String, unique=True)
    newest_semester = Column(String)
    cpa = Column(Float)
    failed_course_number = Column(Integer)
    courses_number = Column(Integer)
    year_level = Column(String)
    warning_level = Column(String)
    level_3_warning_number = Column(Integer)
    department_id = Column(String, ForeignKey("departments.id"))

    department = relationship("Department", back_populates="students")
    learned_subjects = relationship("LearnedSubject", back_populates="student")
    semester_gpas = relationship("SemesterGPA", back_populates="student")
    class_registers = relationship("ClassRegister", back_populates="student")
    subject_registers = relationship("SubjectRegister", back_populates="student")
