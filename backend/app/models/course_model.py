from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.associations import student_course_table

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(50), primary_key=True)
    course_id = Column(String(255), unique=True)
    course_name = Column(String(255))

    course_subjects = relationship("CourseSubject", back_populates="course")
    enrolled_students = relationship("Student", secondary=student_course_table, back_populates="enrolled_courses")
