from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(String(50), primary_key=True)
    subject_id = Column(String(50), ForeignKey("subjects.id"))
    class_id = Column(String(255), unique=True)
    class_name = Column(String(255))
    linked_class_ids = Column(String(255))
    class_type = Column(String(255))
    classroom = Column(String(255))
    study_date = Column(String(255))
    study_time = Column(DateTime)
    max_student_number = Column(Integer)
    teacher_name = Column(String(255))
    study_week = Column(String(255))

    subject = relationship("Subject", back_populates="classes")
    class_registers = relationship("ClassRegister", back_populates="class_info_rel")
