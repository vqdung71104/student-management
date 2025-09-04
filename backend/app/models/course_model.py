from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(50), primary_key=True)
    course_id = Column(String(255), unique=True)
    course_name = Column(String(255))

    course_subjects = relationship("CourseSubject", back_populates="course")
