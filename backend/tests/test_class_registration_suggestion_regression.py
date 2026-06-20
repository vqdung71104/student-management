from copy import deepcopy

from app.schemas.preference_schema import CompletePreference
from app.services.preference_service import PreferenceCollectionService
from app.services.schedule_combination_service import ScheduleCombinationGenerator
from app.services.chatbot_service import ChatbotService


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


def test_merge_constraints_into_preferences_marks_time_answered():
    service = ChatbotService.__new__(ChatbotService)
    prefs = CompletePreference()

    captured = service._merge_constraints_into_preferences(
        preferences=prefs,
        constraints_dict={"forbidden_time_slots": ["morning"]},
    )

    assert "time" in captured
    assert prefs.time.avoid_time_periods == ["morning"]
    assert prefs.time.has_answer is True
    assert "time" not in prefs.get_missing_preferences()
    assert "specific" in prefs.get_missing_preferences()


def _reasoning_subject(code, name, **extra):
    return {
        "id": extra.pop("id", len(code)),
        "subject_id": code,
        "subject_name": name,
        "credits": extra.pop("credits", 3),
        **extra,
    }


def test_combination_reasoning_explains_each_subject_in_priority_order_without_duplicates():
    service = ChatbotService.__new__(ChatbotService)
    failed = _reasoning_subject("IT1000", "Nhập môn lập trình")
    previous = _reasoning_subject("MI1001", "Giải tích", learning_semester=2)
    current = _reasoning_subject("IT2000", "Cấu trúc dữ liệu", learning_semester=3)
    duplicate_current = dict(failed)

    subject_result = {
        "student_semester_number": 3,
        "max_credits_allowed": 24,
        "summary": {
            "semester_match": [current, duplicate_current],
            "failed_retake": [failed],
            "previous_semester_unlearned": [previous],
        },
    }
    suggested = [failed, previous, current]
    classes_by_subject = {subject["subject_id"]: [{"id": subject["id"]}] for subject in suggested}
    formatted_classes = [
        {
            "subject_id": subject["subject_id"],
            "study_date": "Monday",
            "study_time_start": "08:00",
        }
        for subject in suggested
    ]
    original_inputs = deepcopy((formatted_classes, subject_result, suggested, classes_by_subject))

    reasons = service._build_combination_reasoning(
        formatted_classes=formatted_classes,
        combo_metrics={"study_days": 1, "free_days": 6, "earliest_start": "08:00", "latest_end": "11:00"},
        preferences={},
        subject_result=subject_result,
        suggested_subjects=suggested,
        classes_by_subject=classes_by_subject,
    )

    failed_idx = next(i for i, reason in enumerate(reasons) if reason.startswith("IT1000 -"))
    previous_idx = next(i for i, reason in enumerate(reasons) if reason.startswith("MI1001 -"))
    current_idx = next(i for i, reason in enumerate(reasons) if reason.startswith("IT2000 -"))
    assert failed_idx < previous_idx < current_idx
    assert "điểm F" in reasons[failed_idx]
    assert "kỳ 2" in reasons[previous_idx]
    assert "đúng lộ trình kỳ 3" in reasons[current_idx]
    assert sum(reason.startswith("IT1000 -") for reason in reasons) == 1
    assert (formatted_classes, subject_result, suggested, classes_by_subject) == original_inputs


def test_combination_reasoning_distinguishes_credit_option_from_subject_without_classes():
    service = ChatbotService.__new__(ChatbotService)
    option = _reasoning_subject("PE1001", "Giáo dục thể chất", credits=2, option_only=True)
    no_class = _reasoning_subject("SSH1001", "Triết học", credits=3)
    subject_result = {
        "max_credits_allowed": 23,
        "summary": {
            "political": [no_class],
            "physical_education": [option],
        },
    }

    reasons = service._build_combination_reasoning(
        formatted_classes=[],
        combo_metrics={},
        preferences={},
        subject_result=subject_result,
        suggested_subjects=[no_class],
        classes_by_subject={"SSH1001": [], "PE1001": []},
    )

    no_class_reason = next(reason for reason in reasons if reason.startswith("SSH1001 -"))
    option_reason = next(reason for reason in reasons if reason.startswith("PE1001 -"))
    assert "không có lớp khả dụng" in no_class_reason
    assert "không có lớp" not in option_reason
    assert "lựa chọn tham khảo" in option_reason
    assert "vượt mức tối đa 23 TC" in option_reason


def test_combination_reasoning_quantifies_preference_matches():
    service = ChatbotService.__new__(ChatbotService)
    subject = _reasoning_subject("IT2000", "Cấu trúc dữ liệu", learning_semester=3)
    formatted_classes = [
        {"subject_id": "IT2000", "study_date": "Monday", "study_time_start": "08:00"},
        {"subject_id": "MI2000", "study_date": "Saturday", "study_time_start": "13:00"},
    ]

    reasons = service._build_combination_reasoning(
        formatted_classes=formatted_classes,
        combo_metrics={},
        preferences={
            "time_period": "morning",
            "prefer_days": ["Monday"],
            "avoid_days": ["Saturday"],
        },
        subject_result={"student_semester_number": 3, "summary": {"semester_match": [subject]}},
        suggested_subjects=[subject],
        classes_by_subject={"IT2000": [{"id": 1}]},
    )

    assert any("1/2 lớp học vào buổi sáng" in reason for reason in reasons)
    assert any("1/2 lớp rơi vào các ngày bạn ưu tiên" in reason for reason in reasons)
    assert any("1/2 lớp tránh được các ngày bạn không muốn học" in reason for reason in reasons)
