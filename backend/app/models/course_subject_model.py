from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class CourseSubject(Base):
    __tablename__ = "course_subjects"

    id = Column(String(50), primary_key=True)
    subject_id = Column(String(50), ForeignKey("subjects.subject_id"))
    course_id = Column(String(50), ForeignKey("courses.id"))
    subject_name = Column(String(255))

    subject = relationship("Subject", back_populates="course_subjects")
    course = relationship("Course", back_populates="course_subjects")
