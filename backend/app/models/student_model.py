from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.associations import student_course_table

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True)
    student_name = Column(String(255))
    enrolled_year = Column(Integer)
    training_level = Column(String(100))
    learning_status = Column(String(50))
    gender = Column(String(10))
    classes = Column(String(500))  # Might contain multiple class IDs
    intake = Column(Integer)
    email = Column(String(255), unique=True)
    newest_semester = Column(String(20))
    cpa = Column(Float)
    failed_courses_number = Column(Integer)
    courses_number = Column(Integer)
    year_level = Column(String(20))
    warning_level = Column(String(50))
    level_3_warning_number = Column(Integer)
    department_id = Column(String(50), ForeignKey("departments.id"))

    department = relationship("Department", back_populates="students")
    learned_subjects = relationship("LearnedSubject", back_populates="student")
    semester_gpa = relationship("SemesterGPA", back_populates="student")
    class_registers = relationship("ClassRegister", back_populates="student")
    subject_registers = relationship("SubjectRegister", back_populates="student")
    enrolled_courses = relationship("Course", secondary=student_course_table, back_populates="enrolled_students")
