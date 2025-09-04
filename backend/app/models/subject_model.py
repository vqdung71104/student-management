from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(50), primary_key=True)
    department_id = Column(String(50), ForeignKey("departments.id"))
    subject_id = Column(String(50), unique=True)
    subject_name = Column(String(255))
    duration = Column(Integer)
    credits = Column(Integer)
    tuition_fee = Column(Float)
    english_subject_name = Column(String(255))
    weight = Column(Float)

    department = relationship("Department", back_populates="subjects")
    classes = relationship("Class", back_populates="subject")
    learned_subjects = relationship("LearnedSubject", back_populates="subject")
    subject_registers = relationship("SubjectRegister", back_populates="subject")
    course_subjects = relationship("CourseSubject", back_populates="subject")
