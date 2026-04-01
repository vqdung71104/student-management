from app.schemas.preference_schema import CompletePreference
from app.services.preference_service import PreferenceCollectionService
from app.services.schedule_combination_service import ScheduleCombinationGenerator


def test_day_parser_accepts_typo_and_compact_numbers():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="thú 2,3,4",
        question_key="day",
        current_preferences=prefs,
    )

    assert set(updated.day.prefer_days) == {"Monday", "Tuesday", "Wednesday"}


def test_day_parser_accepts_mixed_format():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="thứ 2, 3,4",
        question_key="day",
        current_preferences=prefs,
    )

    assert set(updated.day.prefer_days) == {"Monday", "Tuesday", "Wednesday"}


def test_day_parser_marks_not_important():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="không quan trọng",
        question_key="day",
        current_preferences=prefs,
    )

    assert updated.day.is_not_important is True


def test_schedule_combinations_empty_subjects_returns_empty_list():
    generator = ScheduleCombinationGenerator()

    result = generator.generate_combinations(
        classes_by_subject={"IT3170": []},
        preferences={},
        max_combinations=20,
    )

    assert result == []


def test_continuous_accepts_unaccented_negative_answer():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="khong",
        question_key="continuous",
        current_preferences=prefs,
    )

    assert updated.continuous.prefer_continuous is False
    assert updated.continuous.is_not_important is False


def test_free_days_accepts_unaccented_not_important():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="khong quan trong",
        question_key="free_days",
        current_preferences=prefs,
    )

    assert updated.free_days.is_not_important is True
