from copy import deepcopy
from datetime import time

from app.schemas.preference_schema import CompletePreference
from app.services.preference_service import PreferenceCollectionService
from app.services.schedule_combination_service import ScheduleCombinationGenerator
from app.services.chatbot_service import ChatbotService
from app.services.constraint_extractor import get_constraint_extractor


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


def test_specific_parser_does_not_turn_negative_subject_into_positive():
    service = PreferenceCollectionService()
    prefs = CompletePreference()

    updated = service.parse_user_response(
        response="kh\u00f4ng h\u1ecdc IT4735",
        question_key="specific",
        current_preferences=prefs,
    )

    assert updated.specific.has_answer is True
    assert updated.specific.specific_subjects == []
    assert updated.specific.specific_class_ids == []


def test_constraint_extractor_splits_positive_and_negative_subjects():
    extractor = get_constraint_extractor()

    negative = extractor.extract("kh\u00f4ng h\u1ecdc IT4735", query_type="class_registration_suggestion")
    positive = extractor.extract("mu\u1ed1n h\u1ecdc IT4735", query_type="class_registration_suggestion")
    both = extractor.extract(
        "mu\u1ed1n h\u1ecdc IT4735 nh\u01b0ng kh\u00f4ng h\u1ecdc IT4735",
        query_type="class_registration_suggestion",
    )

    assert negative.exclude_subject_codes == ["IT4735"]
    assert negative.include_subject_codes == []
    assert positive.include_subject_codes == ["IT4735"]
    assert positive.exclude_subject_codes == []
    assert both.exclude_subject_codes == ["IT4735"]
    assert both.include_subject_codes == []


def test_mixed_specific_answer_does_not_create_avoid_day_from_subject_code():
    extractor = get_constraint_extractor()
    pref_service = PreferenceCollectionService()
    chatbot_service = ChatbotService.__new__(ChatbotService)

    question = "kh\u00f4ng h\u1ecdc IT4735, h\u1ecdc gi\u1ea3i t\u00edch 1"
    constraints = extractor.extract(question, query_type="class_registration_suggestion").model_dump()
    prefs = pref_service.extract_initial_preferences(question)

    captured = chatbot_service._merge_constraints_into_preferences(prefs, constraints)

    assert prefs.day.avoid_days == []
    assert constraints["exclude_subject_codes"] == ["IT4735"]
    assert constraints["include_subjects"] == ["giai tich 1"]
    assert "IT4735" not in prefs.specific.specific_subjects
    assert "giai tich 1" in prefs.specific.specific_subjects
    assert "specific" in captured


def test_class_suggestion_question_does_not_autofill_specific_subject():
    extractor = get_constraint_extractor()
    pref_service = PreferenceCollectionService()
    chatbot_service = ChatbotService.__new__(ChatbotService)

    question = "t\u00f4i n\u00ean h\u1ecdc l\u1edbp n\u00e0o k\u1ef3 sau"
    constraints = extractor.extract(question, query_type="class_registration_suggestion").model_dump()
    prefs = pref_service.extract_initial_preferences(question)

    captured = chatbot_service._merge_constraints_into_preferences(prefs, constraints)

    assert constraints["include_subjects"] == []
    assert constraints["include_subject_codes"] == []
    assert prefs.specific.specific_subjects == []
    assert prefs.specific.has_answer is False
    assert "specific" not in captured


def test_constraint_extractor_handles_class_schedule_building_and_teacher_polarity():
    extractor = get_constraint_extractor()

    class_negative = extractor.extract("kh\u00f4ng h\u1ecdc l\u1edbp 123456", query_type="class_registration_suggestion")
    class_positive = extractor.extract("mu\u1ed1n l\u1edbp 123456", query_type="class_registration_suggestion")
    schedule_positive = extractor.extract(
        "chi\u1ec1u th\u1ee9 2, chi\u1ec1u th\u1ee9 3, c\u1ea3 ng\u00e0y th\u1ee9 4",
        query_type="class_registration_suggestion",
    )
    schedule_negative = extractor.extract("kh\u00f4ng h\u1ecdc chi\u1ec1u th\u1ee9 2", query_type="class_registration_suggestion")
    building_negative = extractor.extract("kh\u00f4ng h\u1ecdc \u1edf t\u00f2a D9", query_type="class_registration_suggestion")
    building_positive = extractor.extract("h\u1ecdc \u1edf t\u00f2a D3-5", query_type="class_registration_suggestion")
    teacher_negative = extractor.extract("kh\u00f4ng h\u1ecdc th\u1ea7y A", query_type="class_registration_suggestion")

    assert class_negative.exclude_class_ids == ["123456"]
    assert class_positive.include_class_ids == ["123456"]
    assert [item.model_dump() for item in schedule_positive.include_day_session_constraints] == [
        {"days": ["Monday"], "session": "afternoon"},
        {"days": ["Tuesday"], "session": "afternoon"},
        {"days": ["Wednesday"], "session": None},
    ]
    assert [item.model_dump() for item in schedule_negative.exclude_day_session_constraints] == [
        {"days": ["Monday"], "session": "afternoon"},
    ]
    assert building_negative.exclude_buildings == ["D9"]
    assert building_positive.include_buildings == ["D3-5"]
    assert teacher_negative.exclude_teachers == ["A"]


def test_class_nlq_constraints_filter_negative_hard_and_positive_soft_fallback():
    service = ChatbotService.__new__(ChatbotService)
    classes = [
        {
            "class_id": "111111",
            "class_name": "A",
            "subject_id": "IT4735",
            "subject_name": "IoT",
            "classroom": "D9-401",
            "teacher_name": "Thay A",
            "study_date": "Monday",
            "study_time_start": time(12, 30),
        },
        {
            "class_id": "222222",
            "class_name": "B",
            "subject_id": "IT1111",
            "subject_name": "Other",
            "classroom": "D3-501",
            "teacher_name": "Thay B",
            "study_date": "Tuesday",
            "study_time_start": time(12, 30),
        },
    ]

    negative = {"exclude_subject_codes": ["IT4735"], "exclude_buildings": ["D9"]}
    positive_unavailable = {"include_buildings": ["C1"]}

    assert [cls["class_id"] for cls in service._apply_class_nlq_constraints(classes, negative)] == ["222222"]
    assert service._apply_class_nlq_constraints(classes, positive_unavailable) == classes


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


def test_combination_reasoning_groups_subjects_with_same_explanation_in_vietnamese_list():
    service = ChatbotService.__new__(ChatbotService)
    first = _reasoning_subject("IT3382", "Kỹ năng ITSS học bằng tiếng Nhật 2", learning_semester=8)
    second = _reasoning_subject("IT4542", "Quản trị phát triển phần mềm", learning_semester=8)
    third = _reasoning_subject("IT4930", "Nhập môn Khoa học dữ liệu", learning_semester=8)

    reasons = service._build_combination_reasoning(
        formatted_classes=[
            {"subject_id": subject["subject_id"], "study_date": "Monday"}
            for subject in [first, second, third]
        ],
        combo_metrics={},
        preferences={},
        subject_result={
            "student_semester_number": 8,
            "summary": {"semester_match": [first, second, third]},
        },
        suggested_subjects=[first, second, third],
        classes_by_subject={subject["subject_id"]: [{"id": subject["id"]}] for subject in [first, second, third]},
    )

    grouped_reason = next(reason for reason in reasons if "đúng lộ trình kỳ 8" in reason)
    assert grouped_reason == (
        "IT3382 - Kỹ năng ITSS học bằng tiếng Nhật 2, "
        "IT4542 - Quản trị phát triển phần mềm và "
        "IT4930 - Nhập môn Khoa học dữ liệu "
        "được chọn vì đúng lộ trình kỳ 8, giúp bạn theo sát kế hoạch đào tạo."
    )
    assert sum("đúng lộ trình kỳ 8" in reason for reason in reasons) == 1


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
        {
            "subject_id": "IT2000", "study_date": "Monday",
            "study_time_start": "08:00", "study_time_end": "10:00",
        },
        {
            "subject_id": "MI2000", "study_date": "Saturday",
            "study_time_start": "13:00", "study_time_end": "17:00",
        },
    ]

    reasons = service._build_combination_reasoning(
        formatted_classes=formatted_classes,
        combo_metrics={
            "study_days": 2,
            "free_days": 5,
            "earliest_start": "08:00",
            "latest_end": "17:00",
            "continuous_study_days": 1,
        },
        preferences={
            "time_period": "morning",
            "prefer_days": ["Monday"],
            "avoid_days": ["Saturday"],
            "prefer_free_days": True,
            "prefer_continuous": True,
            "avoid_late_end": True,
        },
        subject_result={"student_semester_number": 3, "summary": {"semester_match": [subject]}},
        suggested_subjects=[subject],
        classes_by_subject={"IT2000": [{"id": 1}]},
    )

    assert any("1/2 lớp học vào buổi sáng" in reason for reason in reasons)
    assert any("1/2 lớp rơi vào các ngày bạn ưu tiên" in reason for reason in reasons)
    assert any("1/2 lớp tránh được các ngày bạn không muốn học" in reason for reason in reasons)
    assert any("đáp ứng mong muốn có nhiều ngày trống" in reason for reason in reasons)
    assert any("thứ 2: 1 môn" in reason and "thứ 7: 1 môn" in reason for reason in reasons)
    assert any("đúng với mong muốn học tập trung" in reason for reason in reasons)
    assert any("2/2 lớp kết thúc không muộn hơn 18:00" in reason for reason in reasons)


def test_schedule_generator_never_returns_time_conflict_as_fallback():
    generator = ScheduleCombinationGenerator()
    classes_by_subject = {
        "IT1000": [{
            "id": 1, "class_id": "IT-A", "subject_id": "IT1000",
            "study_week": [1, 2], "study_date": "Monday",
            "study_time_start": time(8, 0), "study_time_end": time(10, 0), "credits": 3,
        }],
        "MI1000": [{
            "id": 2, "class_id": "MI-A", "subject_id": "MI1000",
            "study_week": [1, 2], "study_date": "Monday",
            "study_time_start": time(9, 0), "study_time_end": time(11, 0), "credits": 3,
        }],
    }

    result = generator.generate_combinations(classes_by_subject, preferences={}, max_combinations=10)

    assert result == []


def test_schedule_generator_rejects_duplicate_subject_even_with_different_source_keys():
    generator = ScheduleCombinationGenerator()
    classes_by_subject = {
        "GROUP_A": [{
            "id": 1, "class_id": "IT-A", "subject_id": "IT1000",
            "study_week": [1], "study_date": "Monday",
            "study_time_start": time(8, 0), "study_time_end": time(9, 0), "credits": 3,
        }],
        "GROUP_B": [{
            "id": 2, "class_id": "IT-B", "subject_id": "IT1000",
            "study_week": [1], "study_date": "Tuesday",
            "study_time_start": time(8, 0), "study_time_end": time(9, 0), "credits": 3,
        }],
    }

    result = generator.generate_combinations(classes_by_subject, preferences={}, max_combinations=10)

    assert result == []


def test_schedule_generator_treats_missing_week_as_potential_overlap():
    generator = ScheduleCombinationGenerator()
    classes = [
        {
            "class_id": "IT-A", "subject_id": "IT1000", "study_week": [],
            "study_date": "Monday", "study_time_start": time(8, 0), "study_time_end": time(10, 0),
        },
        {
            "class_id": "MI-A", "subject_id": "MI1000", "study_week": [1, 2],
            "study_date": "Monday", "study_time_start": time(9, 0), "study_time_end": time(11, 0),
        },
    ]

    assert generator.has_time_conflicts(classes) is True


def test_combination_comparison_explains_class_and_schedule_differences():
    service = ChatbotService.__new__(ChatbotService)
    combinations = [
        {
            "score": 130,
            "classes": [{
                "subject_id": "IT1000", "class_id": "IT-A", "study_date": "Monday",
            }],
            "metrics": {"study_days": 1, "earliest_start": "08:00", "latest_end": "10:00"},
        },
        {
            "score": 120,
            "classes": [{
                "subject_id": "IT1000", "class_id": "IT-B", "study_date": "Tuesday",
            }],
            "metrics": {"study_days": 1, "earliest_start": "13:00", "latest_end": "15:00"},
        },
    ]

    comparison = service._build_combinations_comparison(combinations)

    assert "điểm xếp hạng cao nhất" in comparison[0]
    assert "IT1000: lớp IT-B thay lớp IT-A" in comparison[1]
    assert "thứ 3" in comparison[1]
