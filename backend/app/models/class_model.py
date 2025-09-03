from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    class_id = Column(String, unique=True)
    class_name = Column(String)
    linked_class_ids = Column(String)
    class_type = Column(String)
    classroom = Column(String)
    study_date = Column(String)
    study_time = Column(DateTime)
    max_student_number = Column(Integer)
    teacher_name = Column(String)
    study_week = Column(String)

    subject = relationship("Subject", back_populates="classes")
    class_registers = relationship("ClassRegister", back_populates="class_info_rel")
