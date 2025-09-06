from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ClassRegister(Base):
    __tablename__ = "class_registers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_info = Column(String(255))
    register_type = Column(String(255))
    register_status = Column(String(255))
    student_id = Column(Integer, ForeignKey("students.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))

    student = relationship("Student", back_populates="class_registers")
    class_info_rel = relationship("Class", back_populates="class_registers")
