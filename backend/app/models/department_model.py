from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(String(50), primary_key=True)  # Added length
    name = Column(String(255))  # Added length

    students = relationship("Student", back_populates="department")
    subjects = relationship("Subject", back_populates="department")
