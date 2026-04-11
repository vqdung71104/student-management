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


def test_free_days_negative_answer_marks_as_answered():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="không",
        question_key="free_days",
        current_preferences=prefs,
    )

    assert updated.free_days.prefer_free_days is False
    assert updated.free_days.has_answer is True
    assert 'free_days' not in updated.get_missing_preferences()


def test_free_days_option_2_full_text_marks_as_answered():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="2, không, tôi muốn học đều các ngày",
        question_key="free_days",
        current_preferences=prefs,
    )

    assert updated.free_days.prefer_free_days is False
    assert updated.free_days.has_answer is True
    assert 'free_days' not in updated.get_missing_preferences()


def test_extract_initial_preferences_marks_answered_from_single_input():
    service = PreferenceCollectionService()

    updated = service.extract_initial_preferences(
        "tôi muốn học lớp buổi sáng, học thứ 2 và thứ 4"
    )

    assert updated.time.time_period == "morning"
    assert updated.time.has_answer is True
    assert "Monday" in updated.day.prefer_days
    assert "Wednesday" in updated.day.prefer_days
    assert updated.day.has_answer is True
    assert "time" not in updated.get_missing_preferences()
    assert "day" not in updated.get_missing_preferences()


def test_merge_supplemental_preferences_captures_extra_fields_in_same_reply():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    # User is answering day question but includes extra preferences in same sentence.
    prefs = service.parse_user_response(
        response="Thứ 2, thứ 4 và tôi muốn học muộn, không cần yêu cầu gì thêm",
        question_key="day",
        current_preferences=prefs,
    )

    prefs, captured_keys = service.merge_supplemental_preferences(
        response="Thứ 2, thứ 4 và tôi muốn học muộn, không cần yêu cầu gì thêm",
        current_preferences=prefs,
        skip_keys={"day"},
    )

    assert "time" in captured_keys
    assert "specific" in captured_keys
    assert prefs.time.prefer_late_start is True
    assert prefs.time.has_answer is True
    assert prefs.specific.has_answer is True
    assert "time" not in prefs.get_missing_preferences()
    assert "specific" not in prefs.get_missing_preferences()


def test_specific_parser_accepts_explicit_no_requirement():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="không có yêu cầu",
        question_key="specific",
        current_preferences=prefs,
    )

    assert updated.specific.has_answer is True
    assert updated.specific.preferred_teachers == []
    assert updated.specific.specific_class_ids == []
    assert updated.specific.specific_times is None
    assert "specific" not in updated.get_missing_preferences()


def test_specific_parser_extracts_teacher_class_and_time():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="Thầy Nguyễn Văn A, lớp CS101, từ 7h đến 9h",
        question_key="specific",
        current_preferences=prefs,
    )

    assert updated.specific.has_answer is True
    assert updated.specific.preferred_teachers
    assert any("Nguyễn" in teacher or "Van" in teacher or "Văn" in teacher for teacher in updated.specific.preferred_teachers)
    assert "CS101" in updated.specific.specific_class_ids
    assert updated.specific.specific_times == {"start": "07:00", "end": "09:00"}
    assert "specific" not in updated.get_missing_preferences()


def test_specific_parser_extracts_specific_subjects():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="Môn IT3170, học phần cấu trúc dữ liệu",
        question_key="specific",
        current_preferences=prefs,
    )

    assert updated.specific.has_answer is True
    assert "IT3170" in updated.specific.specific_subjects
    assert any("cấu trúc dữ liệu" in subject.lower() for subject in updated.specific.specific_subjects)
    assert "specific" not in updated.get_missing_preferences()


def test_specific_parser_rejects_unparseable_response():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="xyz abc 123",
        question_key="specific",
        current_preferences=prefs,
    )

    assert updated.specific.has_answer is False
    assert updated.specific.preferred_teachers == []
    assert updated.specific.specific_class_ids == []
    assert updated.specific.specific_times is None
    assert "specific" in updated.get_missing_preferences()
