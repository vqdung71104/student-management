from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class LearnedSubject(Base):
    __tablename__ = "learned_subjects"

    id = Column(String, primary_key=True)
    subject_name = Column(String)
    credits = Column(Integer)
    final_score = Column(Float)
    midterm_score = Column(Float)
    weight = Column(Float)
    total_score = Column(Float)
    letter_grade = Column(String)
    semester = Column(String)
    student_id = Column(String, ForeignKey("students.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="learned_subjects")
    subject = relationship("Subject", back_populates="learned_subjects")
