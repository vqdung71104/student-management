from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True)
    name = Column(String)

    students = relationship("Student", back_populates="department")
    subjects = relationship("Subject", back_populates="department")
