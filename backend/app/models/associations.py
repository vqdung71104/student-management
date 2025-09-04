# backend/app/models/associations.py
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from app.db.database import Base

student_course_table = Table(
    "student_course",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", String(50), ForeignKey("courses.id"), primary_key=True)
)

subject_condition_table = Table(
    "subject_condition",
    Base.metadata,
    Column("subject_id", ForeignKey("subjects.subject_id"), primary_key=True),
    Column("condition_subject_id", ForeignKey("subjects.subject_id"), primary_key=True)
)

linked_class_table = Table(
    "linked_class",
    Base.metadata,
    Column("class_id", ForeignKey("classes.class_id"), primary_key=True),
    Column("linked_class_id", ForeignKey("classes.class_id"), primary_key=True)
)
