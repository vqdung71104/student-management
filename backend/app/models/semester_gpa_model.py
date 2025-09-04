from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SemesterGPA(Base):
    __tablename__ = "semester_gpa"

    id = Column(String(50), primary_key=True)
    semester = Column(String(255))
    gpa = Column(Float)
    student_id = Column(String(50), ForeignKey("students.id"))

    student = relationship("Student", back_populates="semester_gpas")
