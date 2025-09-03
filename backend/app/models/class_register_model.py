from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ClassRegister(Base):
    __tablename__ = "class_registers"

    id = Column(String, primary_key=True)
    class_info = Column(String)
    register_type = Column(String)
    register_status = Column(String)
    student_id = Column(String, ForeignKey("students.id"))
    class_id = Column(String, ForeignKey("classes.id"))

    student = relationship("Student", back_populates="class_registers")
    class_info_rel = relationship("Class", back_populates="class_registers")
