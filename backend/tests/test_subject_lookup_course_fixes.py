import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.course_model import Course
from app.models.course_subject_model import CourseSubject
from app.models.class_model import Class
from app.models.department_model import Department
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.services.chatbot_service import ChatbotService


@pytest.fixture()
def lookup_context():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    department = Department(id="D01", name="Test")
    course = Course(course_id="KTEST", course_name="Test course")
    session.add_all([department, course])
    session.flush()
    student = Student(
        student_name="Test Student",
        email="lookup@example.com",
        password="hashed",
        course_id=course.id,
        department_id=department.id,
    )
    outside = Subject(
        subject_id="CS9999",
        subject_name="Unrelated exact-code subject",
        credits=3,
        conditional_subjects="PRE1000",
    )
    inside = Subject(
        subject_id="IT0001",
        subject_name="Cấu trúc dữ liệu",
        credits=3,
        conditional_subjects=None,
    )
    session.add_all([student, outside, inside])
    session.flush()
    session.add(CourseSubject(course_id=course.id, subject_id=inside.id, learning_semester=2))
    session.commit()

    service = ChatbotService(session)
    yield service, student, course, inside, outside
    session.close()
    engine.dispose()


def test_exact_subject_code_is_authoritative_over_in_course_fuzzy_candidate(lookup_context):
    service, _, course, _, outside = lookup_context

    matched = service._resolve_subject_match(
        "thông tin môn CS9999 cấu trúc dữ liệu",
        course.id,
    )

    assert matched is not None
    assert matched["subject_db_id"] == outside.id


def test_fuzzy_subject_id_uses_course_aware_cache_shape(lookup_context):
    service, _, course, inside, _ = lookup_context

    matched = service._fuzzy_matcher.match_subject_by_id(
        "IT001",
        db=service.db,
        preferred_course_id=course.id,
    )

    assert matched is not None
    assert matched.subject_id == inside.subject_id


def test_roman_and_arabic_suffixes_match_and_prefer_course(lookup_context):
    service, _, course, _, _ = lookup_context
    in_course = Subject(subject_id="MI1114", subject_name="Giải tích I", credits=3)
    outside_duplicates = [
        Subject(subject_id=f"MI9{idx:03d}", subject_name="Giải tích I", credits=3)
        for idx in range(12)
    ]
    service.db.add_all(outside_duplicates + [in_course])
    service.db.flush()
    service.db.add(
        CourseSubject(course_id=course.id, subject_id=in_course.id, learning_semester=1)
    )
    service.db.commit()
    service._fuzzy_matcher.refresh_cache(service.db)

    arabic_match = service._resolve_subject_match("thông tin môn Giải tích 1", course.id)
    roman_match = service._resolve_subject_match("thông tin môn Giải tích I", course.id)

    assert service._fuzzy_matcher._normalize("Giải tích I") == "giai tich 1"
    assert arabic_match["subject_db_id"] == in_course.id
    assert roman_match["subject_db_id"] == in_course.id


def test_unrelated_in_course_match_does_not_hide_best_global_name(lookup_context):
    service, _, course, inside, outside = lookup_context
    outside.subject_name = "Văn hóa kinh doanh và tinh thần khởi nghiệp"
    service.db.add(
        Class(subject_id=inside.id, class_id="167853", class_name="Mạng máy tính")
    )
    service.db.commit()
    service._fuzzy_matcher.refresh_cache(service.db)

    matched = service._resolve_subject_match(
        "thông tin môn văn hóa kinh doạn và tinh thần khời nghiệp",
        course.id,
    )

    assert matched is not None
    assert matched["subject_db_id"] == outside.id


def test_exact_class_code_prefers_in_course_duplicate(lookup_context):
    service, _, course, inside, outside = lookup_context
    service.db.add_all([
        Class(subject_id=outside.id, class_id="123456", class_name="Outside class"),
        Class(subject_id=inside.id, class_id="123456", class_name="In-course class"),
    ])
    service.db.commit()

    matched = service._resolve_class_match("thông tin lớp 123456", course.id)

    assert matched is not None
    assert matched["subject_db_id"] == inside.id
    assert matched["source"] == "class_id_exact"


def test_exact_outside_class_code_beats_in_course_fuzzy_class(lookup_context):
    service, _, course, inside, outside = lookup_context
    service.db.add_all([
        Class(subject_id=outside.id, class_id="654321", class_name="Outside exact"),
        Class(subject_id=inside.id, class_id="654320", class_name="In-course fuzzy"),
    ])
    service.db.commit()
    service._fuzzy_matcher.refresh_cache(service.db)

    matched = service._resolve_class_match("thông tin lớp 654321", course.id)

    assert matched is not None
    assert matched["subject_db_id"] == outside.id
    assert matched["source"] == "class_id_exact"


def test_outside_subject_status_is_not_taken_out_of_program(lookup_context):
    service, student, _, _, outside = lookup_context

    rows = service._build_subject_info_rows(outside.id, student.id, student.course_id)

    assert rows[0]["learning_status"] == "Không thuộc chương trình học"
    assert rows[0]["conditional_subjects"] == "PRE1000"


@pytest.mark.asyncio
async def test_known_subject_without_classes_returns_specific_message(lookup_context):
    service, student, _, inside, _ = lookup_context

    result = await service.process_class_info(student.id, f"môn {inside.subject_id} có mở kỳ này không")

    assert result is not None
    assert result["data"] == []
    assert result["text"] == f"Không có lớp của môn {inside.subject_name} ({inside.subject_id}) đang mở kỳ này."
