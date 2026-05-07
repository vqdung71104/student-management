import types
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.db.database import Base
from app.middleware.rate_limit import RATE_LIMIT_TIERS, rate_limit, RateLimitExceeded
from app.models.chat_history_model import ChatConversation
from app.models.course_model import Course
from app.models.department_model import Department
from app.models.student_model import Student
from app.rules.subject_suggestion_rules import SubjectSuggestionRuleEngine
from app.services.chat_history_service import ChatHistoryService


def test_subject_improvement_skips_zero_credit_subjects():
    engine = SubjectSuggestionRuleEngine(db=types.SimpleNamespace(execute=lambda *args, **kwargs: None))

    class DummyResult:
        def fetchall(self):
            return []

    engine.db = types.SimpleNamespace(execute=lambda *args, **kwargs: DummyResult())

    subjects = [
        {"subject_id": "SUB0", "subject_name": "Zero Credit", "credits": 0},
        {"subject_id": "SUB3", "subject_name": "Three Credit", "credits": 3},
    ]
    student_data = {
        "completed_subjects": {
            "SUB0": {"grade": "D", "subject_name": "Zero Credit", "credits": 0},
            "SUB3": {"grade": "D", "subject_name": "Three Credit", "credits": 3},
        }
    }

    improvements = engine.rule_7_filter_grade_improvement(
        subjects=subjects,
        student_data=student_data,
        current_total_credits=0,
        student_id=1,
    )

    improvement_ids = {item["subject_id"] for item in improvements}
    assert "SUB0" not in improvement_ids
    assert "SUB3" in improvement_ids


def test_rate_limit_defaults_are_updated():
    assert RATE_LIMIT_TIERS == [
        ("per_minute", 15, 60),
        ("per_hour", 200, 3600),
        ("per_day", 300, 86400),
    ]


@pytest.mark.asyncio
async def test_rate_limit_blocks_on_16th_request(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "15")
    monkeypatch.setenv("RATE_LIMIT_PER_HOUR", "200")
    monkeypatch.setenv("RATE_LIMIT_PER_DAY", "300")

    class DummyStudent:
        def __init__(self, student_id: int):
            self.id = student_id

    @rate_limit()
    async def limited_route(student: DummyStudent):
        return "ok"

    student = DummyStudent(999001)
    for _ in range(15):
        assert await limited_route(student=student) == "ok"

    with pytest.raises(RateLimitExceeded) as exc_info:
        await limited_route(student=student)

    assert exc_info.value.tier == "per_minute"
    assert exc_info.value.limit == 15


def _create_test_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def _seed_student(session):
    department = Department(id="D01", name="Dept")
    course = Course(course_id="K65", course_name="Course 65")
    session.add_all([department, course])
    session.flush()

    student = Student(
        student_name="Test Student",
        email="test.student@example.com",
        password="hashed",
        course_id=course.id,
        department_id=department.id,
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def test_rename_conversation_updates_database():
    session = _create_test_session()
    student = _seed_student(session)
    service = ChatHistoryService(session)

    conversation = ChatConversation(id=1, student_pk=student.id, title="Old title")
    session.add(conversation)
    session.commit()
    updated = service.rename_conversation(
        student_pk=student.id,
        conversation_id=conversation.id,
        title="New title",
    )

    loaded = session.query(ChatConversation).filter(ChatConversation.id == conversation.id).first()
    assert updated.title == "New title"
    assert loaded is not None
    assert loaded.title == "New title"


def test_delete_conversation_updates_database():
    session = _create_test_session()
    student = _seed_student(session)
    service = ChatHistoryService(session)

    conversation = ChatConversation(id=2, student_pk=student.id, title="To delete")
    session.add(conversation)
    session.commit()
    service.delete_conversation(student_pk=student.id, conversation_id=conversation.id)

    loaded = session.query(ChatConversation).filter(ChatConversation.id == conversation.id).first()
    assert loaded is None
