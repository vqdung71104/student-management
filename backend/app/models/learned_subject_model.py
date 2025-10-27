from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class LearnedSubject(Base):
    __tablename__ = "learned_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(String(255))
    credits = Column(Integer)
    letter_grade = Column(String(10))  # Chỉ giữ lại letter_grade
    semester = Column(String(255))
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="learned_subjects")
    subject = relationship("Subject", back_populates="learned_subjects")
