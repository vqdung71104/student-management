"""
Regression tests for class_info constraint extraction.
"""

from app.services.constraint_extractor import get_constraint_extractor
from app.services.nl2sql_service import NL2SQLService


def test_extract_class_id_from_natural_phrase():
    extractor = get_constraint_extractor()
    c = extractor.extract("thông tin lớp 762021", query_type="class_info")

    assert "762021" in c.class_ids
    assert "762021" not in c.subject_names


def test_extract_class_name_from_explicit_label():
    extractor = get_constraint_extractor()
    c = extractor.extract("tìm theo tên lớp: KTPM 01 - Sáng", query_type="class_info")

    assert any("KTPM 01" in name for name in c.class_names)


def test_extract_subject_id_from_explicit_label():
    extractor = get_constraint_extractor()
    c = extractor.extract("xem class có subject_id 123", query_type="class_info")

    assert 123 in c.subject_ids


def test_compound_subject_name_is_not_split_on_and():
    extractor = get_constraint_extractor()
    c = extractor.extract(
        "các lớp của môn Cấu trúc dữ liệu và giải thuật",
        query_type="class_info",
    )

    assert c.subject_names == ["cấu trúc dữ liệu và giải thuật"]


def test_nl2sql_does_not_turn_compound_subject_name_into_a_list():
    service = NL2SQLService.__new__(NL2SQLService)

    names = service._extract_subject_name_list(
        "các lớp của môn Cấu trúc dữ liệu và giải thuật"
    )

    assert names == []
