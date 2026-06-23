import os
import sys
import types

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.db.database import Base
from app.models.class_model import Class
from app.models.course_model import Course
from app.models.department_model import Department
from app.models.learned_subject_model import LearnedSubject
from app.models.semester_gpa_model import SemesterGPA
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.routes.learned_subject_routes import update_semester_gpa, update_student_stats
from app.services.elective_service import ElectiveModuleService, validate_student_choices


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def test_shared_subject_does_not_trigger_module_conflict():
    result = validate_student_choices(["IT4409"], "IT4210", course_id="IT-E6")

    assert result["is_valid"] is True
    assert result["warning_message"] == ""


def test_unique_subject_mix_triggers_module_conflict():
    result = validate_student_choices(["IT3190"], "IT4210", course_id="IT-E6")

    assert result["is_valid"] is False
    assert "waste tuition fees" in result["warning_message"]


def test_target_module_tie_defaults_to_first_module():
    service = ElectiveModuleService()

    progress = service.analyze_progress("IT-E6", passed_subject_ids=[])

    assert progress["target_module"]["module_id"] == "module_1"


def test_completed_module_excludes_other_module_unique_subjects_from_cpa_set():
    service = ElectiveModuleService()
    learned_subjects = [
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4409")),
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4785")),
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4542")),
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4930")),
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT3190")),
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4441")),
        types.SimpleNamespace(letter_grade="D", subject=types.SimpleNamespace(subject_id="IT4210")),
        types.SimpleNamespace(letter_grade="B", subject=types.SimpleNamespace(subject_id="MI1114")),
    ]

    recognized = service.recognized_subject_ids_for_cpa("IT-E6", learned_subjects)

    assert recognized is not None
    assert "IT4210" not in recognized
    assert "MI1114" in recognized
    assert {"IT4409", "IT4785", "IT4542", "IT4930", "IT3190", "IT4441"} <= recognized


def test_uncompleted_module_keeps_all_subjects_in_cpa_set():
    service = ElectiveModuleService()
    learned_subjects = [
        types.SimpleNamespace(letter_grade="A", subject=types.SimpleNamespace(subject_id="IT4409")),
        types.SimpleNamespace(letter_grade="D", subject=types.SimpleNamespace(subject_id="IT4210")),
    ]

    assert service.recognized_subject_ids_for_cpa("IT-E6", learned_subjects) is None


def test_filter_subject_suggestions_prefers_default_module_and_reports_alternatives():
    service = ElectiveModuleService()
    subjects = [
        {"subject_id": "IT3190", "subject_name": "Module 1 unique", "credits": 3},
        {"subject_id": "IT4210", "subject_name": "Module 2 unique", "credits": 3},
        {"subject_id": "IT4409", "subject_name": "Shared", "credits": 3},
    ]

    filtered, progress = service.filter_subjects_for_target_module(
        "IT-E6",
        subjects,
        completed_subjects={},
    )

    assert [subject["subject_id"] for subject in filtered] == ["IT3190", "IT4409"]
    assert progress["target_module"]["module_id"] == "module_1"
    assert progress["alternatives"]


def test_update_student_stats_filters_cpa_after_module_completion_but_keeps_semester_gpa():
    db = _session()
    department = Department(id="D01", name="Dept")
    course = Course(course_id="IT-E6", course_name="Course")
    db.add_all([department, course])
    db.flush()

    student = Student(
        student_name="Module Student",
        email="module.student@example.com",
        password="hashed",
        course_id=course.id,
        department_id=department.id,
    )
    db.add(student)

    subjects = {}
    for subject_id, credits in {
        "IT4409": 3,
        "IT4785": 3,
        "IT4542": 3,
        "IT4930": 3,
        "IT3190": 3,
        "IT4441": 3,
        "IT4210": 3,
        "IT4735": 3,
        "MI1114": 2,
    }.items():
        subject = Subject(subject_id=subject_id, subject_name=subject_id, credits=credits)
        db.add(subject)
        subjects[subject_id] = subject
    db.flush()

    grades = {
        "IT4409": "A",
        "IT4785": "A",
        "IT4542": "A",
        "IT4930": "A",
        "IT3190": "A",
        "IT4441": "A",
        "IT4210": "D",
        "IT4735": "F",
        "MI1114": "B",
    }
    for subject_id, grade in grades.items():
        subject = subjects[subject_id]
        db.add(
            LearnedSubject(
                subject_name=subject.subject_name,
                credits=subject.credits,
                letter_grade=grade,
                semester="20251",
                student_id=student.id,
                subject_id=subject.id,
            )
        )
    db.commit()

    update_semester_gpa(student.id, "20251", db)
    update_student_stats(student.id, db)
    db.commit()

    semester_gpa = db.query(SemesterGPA).filter(SemesterGPA.student_id == student.id).one()
    db.refresh(student)

    assert semester_gpa.total_credits == 26
    assert round(semester_gpa.gpa, 2) == 3.12
    assert student.total_failed_credits == 3
    assert student.failed_subjects_number == 1
    assert student.total_learned_credits == 20
    assert round(student.cpa, 2) == 3.90
