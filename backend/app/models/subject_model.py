from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(50), unique=True, nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"))
    subject_name = Column(String(255))
    duration = Column(String(50))
    credits = Column(Integer)
    tuition_fee = Column(Integer)
    english_subject_name = Column(String(255))
    weight = Column(Float)
    conditional_subjects = Column(String(255), nullable=True)

    department = relationship("Department", back_populates="subjects")
    classes = relationship("Class", back_populates="subject")
    learned_subjects = relationship("LearnedSubject", back_populates="subject")
    subject_registers = relationship("SubjectRegister", back_populates="subject")
    course_subjects = relationship("CourseSubject", back_populates="subject")
    projects = relationship("StudentProjects", back_populates="subject")
