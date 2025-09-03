from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SemesterGPA(Base):
    __tablename__ = "semester_gpa"

    id = Column(String, primary_key=True)
    semester = Column(String)
    gpa = Column(Float)
    student_id = Column(String, ForeignKey("students.id"))

    student = relationship("Student", back_populates="semester_gpas")
