"""
Regression tests for class_info constraint extraction.
"""

from app.services.constraint_extractor import get_constraint_extractor


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
