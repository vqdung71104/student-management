from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.associations import student_course_table


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, nullable=False)  # MSSV
    student_name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_year = Column(Integer, nullable=False)
    training_level = Column(String(100), nullable=False, default="Cử nhân")  # enum-like
    learning_status = Column(String(50), nullable=False, default="Đang học")  # enum-like
    gender = Column(String(10), nullable=False)  # enum-like
    classes = Column(String(500))  #ví dụ: Việt Nhật 01
    email = Column(String(255), unique=True, nullable=False)  # auto-generate
    login_password = Column(String(255), nullable=False, default="e10adc3949ba59abbe56e057f20f883e")  # MD5 của "123456"
    password_updated_at = Column(DateTime, default=func.now(), nullable=True)  # Thời gian đổi mật khẩu gần nhất
    newest_semester = Column(String(20))
    cpa = Column(Float, default=0.0)
    failed_subjects_number = Column(Integer, default=0)
    study_subjects_number = Column(Integer, default=0)
    total_learned_credits = Column(Integer, default=0)
    total_failed_credits = Column(Integer, default=0)
    year_level = Column(String(20), default="Trình độ năm 1")  #enum-like
    warning_level = Column(String(50), default="Cảnh cáo mức 0")  #enum-like
    level_3_warning_number = Column(Integer, default=0)
    department_id = Column(String(50), ForeignKey("departments.id"))

    # Relationships
    department = relationship("Department", back_populates="students")
    learned_subjects = relationship("LearnedSubject", back_populates="student")
    semester_gpa = relationship("SemesterGPA", back_populates="student")
    class_registers = relationship("ClassRegister", back_populates="student")
    subject_registers = relationship("SubjectRegister", back_populates="student")
    enrolled_courses = relationship(
        "Course", secondary=student_course_table, back_populates="enrolled_students"
    )
    drl_records = relationship("StudentDRL", back_populates="student")
    projects = relationship("StudentProjects", back_populates="student")
    scholarship_applications = relationship("ScholarshipApplication", back_populates="student")
