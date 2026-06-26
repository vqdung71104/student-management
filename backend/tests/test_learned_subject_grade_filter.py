import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.chatbot_service import ChatbotService
from app.services.nl2sql_service import NL2SQLService


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("các học phần bị F", "F"),
        ("các học phần bị trượt", "F"),
        ("các môn cần học lại", "F"),
        ("các học phần bị C", "C"),
        ("các học phần bị C+", "C+"),
        ("môn đã học điểm D+", "D+"),
    ],
)
def test_chatbot_service_extracts_learned_subject_grade_filter(query, expected):
    service = ChatbotService.__new__(ChatbotService)

    assert service._extract_learned_subject_grade_filter(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        "điểm các môn đã học",
        "điểm từng môn",
        "xem điểm chi tiết",
    ],
)
def test_chatbot_service_detects_broad_learned_subject_list_query(query):
    service = ChatbotService.__new__(ChatbotService)

    assert service._is_broad_learned_subject_list_query(query) is True


def test_chatbot_service_does_not_treat_specific_score_query_as_broad_list():
    service = ChatbotService.__new__(ChatbotService)

    assert service._is_broad_learned_subject_list_query("điểm môn tiếng nhật 6") is False


def test_nl2sql_extracts_grade_without_fake_subject_name():
    service = NL2SQLService()

    entities = service._extract_entities("các học phần bị C")

    assert entities["letter_grade"] == "C"
    assert "subject_name" not in entities


@pytest.mark.asyncio
async def test_nl2sql_filters_learned_subjects_by_letter_grade():
    service = NL2SQLService()

    result = await service.generate_sql("các học phần bị trượt", "learned_subjects_view", student_id=1)

    assert result["intent"] == "learned_subjects_view"
    assert result["entities"]["letter_grade"] == "F"
    assert "UPPER(ls.letter_grade) = 'F'" in result["sql"]
    assert "s.subject_name LIKE" not in result["sql"]
