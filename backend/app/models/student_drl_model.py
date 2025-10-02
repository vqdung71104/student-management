from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class StudentDRL(Base):
    __tablename__ = "student_drl"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), ForeignKey("students.student_id"), nullable=False)
    semester = Column(Integer, nullable=False)  # Kỳ học (1,2,3...14)
    drl_score = Column(Integer, nullable=False)  # Điểm rèn luyện (-50 đến 100) 
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    student = relationship("Student", back_populates="drl_records")