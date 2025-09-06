from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class CourseSubject(Base):
    __tablename__ = "course_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    subject = relationship("Subject", back_populates="course_subjects")
    course = relationship("Course", back_populates="course_subjects")
