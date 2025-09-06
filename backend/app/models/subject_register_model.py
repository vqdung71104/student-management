from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SubjectRegister(Base):
    __tablename__ = "subject_registers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_name = Column(String(255))
    credits = Column(Integer)
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="subject_registers")
    subject = relationship("Subject", back_populates="subject_registers")
