from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SubjectRegister(Base):
    __tablename__ = "subject_registers"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id"))
    subject_name = Column(String)
    credits = Column(Integer)
    subject_id = Column(String, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="subject_registers")
    subject = relationship("Subject", back_populates="subject_registers")
