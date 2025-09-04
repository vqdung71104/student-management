from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SemesterGPA(Base):
    __tablename__ = "semester_gpa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semester = Column(String(255))
    gpa = Column(Float)
    student_id = Column(Integer, ForeignKey("students.id"))

    student = relationship("Student", back_populates="semester_gpa")
