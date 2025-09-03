from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    course_id = Column(String, unique=True)
    course_name = Column(String)

    course_subjects = relationship("CourseSubject", back_populates="course")
