# backend/app/models/associations.py
from sqlalchemy import Table, Column, ForeignKey
from app.db.database import Base

student_course_table = Table(
    "student_course",
    Base.metadata,
    Column("student_id", ForeignKey("students.student_id"), primary_key=True),
    Column("course_id", ForeignKey("courses.course_id"), primary_key=True)
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
