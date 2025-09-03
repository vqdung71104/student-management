from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class CourseSubject(Base):
    __tablename__ = "course_subjects"

    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    subject_name = Column(String)

    subject = relationship("Subject", back_populates="course_subjects")
    course = relationship("Course", back_populates="course_subjects")
