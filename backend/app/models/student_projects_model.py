from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.enums import ProjectType, ProjectStatus
from datetime import datetime


class StudentProjects(Base):
    __tablename__ = "student_projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(255), ForeignKey("students.student_id"), nullable=False)
    subject_id = Column(String(255), ForeignKey("subjects.subject_id"), nullable=False)
    type = Column(Enum(ProjectType), nullable=False)
    teacher_name = Column(String(255), nullable=False)
    topic = Column(Text, nullable=False)
    scores = Column(Integer, nullable=True)  # Điểm từ 0-100
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    student = relationship("Student", back_populates="projects")
    subject = relationship("Subject", back_populates="projects")