import sys
from pathlib import Path

import pytest

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.graph_nodes import _metadata_to_dict, intent_router_node, query_splitter_node
from app.routes.chatbot_routes import _extract_agent_class_suggestion_fields, _process_single_query
from app.schemas.chatbot_schema import ClassSuggestionMetadata
from app.schemas.preference_schema import PREFERENCE_QUESTIONS


class _NoDbExecute:
    def execute(self, *args, **kwargs):
        raise AssertionError("Unexpected DB execute call in case-matrix tests")


class _FakeChatbotService:
    async def process_grade_view(self, student_id):
        return {
            "text": "CPA hiện tại là 3.20",
            "intent": "grade_view",
            "confidence": "high",
            "data": [{"cpa": 3.2}],
            "metadata": {},
            "error": None,
        }

    async def process_student_info(self, student_id):
        return {
            "text": "Thông tin sinh viên",
            "intent": "student_info",
            "confidence": "high",
            "data": [{"student_id": student_id}],
            "metadata": {},
            "error": None,
        }

    async def process_graduation_progress(self, student_id):
        return {
            "text": "Bạn còn thiếu 2 học phần.",
            "intent": "graduation_progress",
            "confidence": "high",
            "data": [
                {"subject_id": "MI1111", "subject_name": "Giải tích 1"},
                {"subject_id": "IT1111", "subject_name": "Nhập môn CNTT"},
            ],
            "metadata": {"summary": {"missing_count": 2}},
            "error": None,
        }

    async def process_subject_info(self, student_id, question):
        return {
            "text": "Thông tin môn Giải tích 1",
            "intent": "subject_info",
            "confidence": "high",
            "data": [
                {"subject_id": "MI1114", "subject_name": "Giải tích 1", "in_program": True},
                {"subject_id": "MATH101", "subject_name": "Calculus 1", "in_program": False},
            ],
            "metadata": {},
            "error": None,
        }

    async def process_subject_suggestion(self, student_id, question):
        if "JP3110" in question or "jp3110" in question:
            data = [{"subject_id": "MI1114", "subject_name": "Giải tích 1", "reason": "Nên học kỳ sau"}]
        else:
            data = [
                {"subject_id": "MI1114", "subject_name": "Giải tích 1", "reason": "Nên học kỳ sau"},
                {"subject_id": "IT2000", "subject_name": "Cấu trúc dữ liệu", "reason": "Nền tảng quan trọng"},
            ]
        return {
            "text": "Các học phần nên học (kèm lý do).",
            "intent": "subject_registration_suggestion",
            "confidence": "high",
            "data": data,
            "metadata": {},
            "error": None,
        }

    async def process_class_suggestion(self, student_id, question, conversation_id=None, extracted_constraints=None):
        return {
            "text": "Bạn vui lòng chọn preference để hệ thống gợi ý TKB tối ưu.",
            "intent": "class_registration_suggestion",
            "confidence": "high",
            "data": [],
            "metadata": {
                "question_type": "single_choice",
                "question_options": ["Sáng", "Chiều", "Tối"],
                "conversation_state": "collecting",
                "is_preference_collecting": True,
            },
            "question_type": "single_choice",
            "question_options": ["Sáng", "Chiều", "Tối"],
            "conversation_state": "collecting",
            "is_preference_collecting": True,
            "error": None,
        }


async def _split_and_route(user_text: str):
    split_result = await query_splitter_node({"user_text": user_text, "node_trace": []})
    route_result = await intent_router_node(
        {
            "segments": split_result["segments"],
            "current_segment_index": 0,
            "node_trace": [],
        }
    )
    return split_result, route_result


def test_first_day_preference_is_exposed_as_multi_choice_from_agent_result():
    day_question = PREFERENCE_QUESTIONS["day"]
    metadata = {
        "ui": {"title": "Gợi ý lớp"},
        "conversation": {
            "stage": "collecting",
            "next_step": "ask_next_question",
            "current_question": day_question.model_dump(),
        },
        "preferences": {"captured": [], "missing": [], "auto_captured_keys": [], "summary": {}},
    }
    raw = [{
        "raw_result": {
            "status": "success",
            "data": {
                "text": day_question.question,
                "intent": "class_registration_suggestion",
                "data": None,
            },
            "metadata": metadata,
        }
    }]

    data, extracted_metadata = _extract_agent_class_suggestion_fields(
        raw,
        "class_registration_suggestion",
    )

    assert data is None
    current_question = extracted_metadata["conversation"]["current_question"]
    assert current_question["key"] == "day"
    assert current_question["type"] == "multi_choice"
    assert current_question["options"] == [
        "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"
    ]


def test_first_day_preference_is_extracted_from_langgraph_raw_dict():
    day_question = PREFERENCE_QUESTIONS["day"]
    metadata = {
        "conversation": {
            "stage": "collecting",
            "current_question": day_question.model_dump(),
        }
    }
    graph_raw = {
        "status": "success",
        "data": {
            "text": day_question.question,
            "data": None,
            "metadata": metadata,
        },
    }

    data, extracted_metadata = _extract_agent_class_suggestion_fields(
        graph_raw,
        "class_registration_suggestion",
    )

    assert data is None
    current_question = extracted_metadata["conversation"]["current_question"]
    assert current_question["key"] == "day"
    assert current_question["type"] == "multi_choice"
    assert current_question["options"] == day_question.options


def test_langgraph_bridge_preserves_pydantic_question_metadata():
    day_question = PREFERENCE_QUESTIONS["day"]
    validated_metadata = ClassSuggestionMetadata(
        conversation={
            "stage": "collecting",
            "next_step": "ask_next_question",
            "current_question": day_question.model_dump(),
        },
        preferences={
            "captured": [],
            "missing": [{"key": "day", "label": "Ngày học", "hint": "Chọn ngày"}],
            "auto_captured_keys": [],
            "summary": {},
        },
    )

    normalized = _metadata_to_dict(validated_metadata)

    assert normalized["conversation"]["current_question"]["type"] == "multi_choice"
    assert normalized["conversation"]["current_question"]["options"] == day_question.options
    assert normalized["preferences"]["missing"][0]["key"] == "day"


@pytest.mark.asyncio
async def test_case_1_cpa_rulebase_fast_no_agent():
    split_result, route_result = await _split_and_route("cpa")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "grade_view"
    assert route_result["needs_agent"] is False


@pytest.mark.asyncio
async def test_case_2_hello_rulebase_no_agent():
    split_result, route_result = await _split_and_route("hello")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "greeting"
    assert route_result["needs_agent"] is False


@pytest.mark.asyncio
async def test_case_3_graduation_progress_returns_missing_subjects():
    split_result, route_result = await _split_and_route("còn bao nhiêu môn nữa thì tốt nghiệp")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "graduation_progress"

    response = await _process_single_query(
        normalized_text="con bao nhieu mon nua thi tot nghiep",
        student_id=1,
        conversation_id=11,
        db=_NoDbExecute(),
        chatbot_service=_FakeChatbotService(),
        forced_intent="graduation_progress",
    )
    assert response.intent == "graduation_progress"
    assert isinstance(response.data, list) and len(response.data) == 2


@pytest.mark.asyncio
async def test_case_4_subject_info_giai_tich():
    split_result, route_result = await _split_and_route("thông tin môn Giải tích 1")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "subject_info"

    response = await _process_single_query(
        normalized_text="thong tin mon giai tich 1",
        student_id=1,
        conversation_id=11,
        db=_NoDbExecute(),
        chatbot_service=_FakeChatbotService(),
        forced_intent="subject_info",
    )
    assert response.intent == "subject_info"
    assert response.data[0]["in_program"] is True


@pytest.mark.asyncio
async def test_case_5_subject_registration_suggestion():
    split_result, route_result = await _split_and_route("Tôi nên đăng ký học phần nào kỳ sau")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "subject_registration_suggestion"

    response = await _process_single_query(
        normalized_text="toi nen dang ky hoc phan nao ky sau",
        student_id=1,
        conversation_id=11,
        db=_NoDbExecute(),
        chatbot_service=_FakeChatbotService(),
        forced_intent="subject_registration_suggestion",
    )
    assert response.intent == "subject_registration_suggestion"
    assert "lý do" in response.text.lower() or "ly do" in response.text.lower()


@pytest.mark.asyncio
async def test_case_6_class_registration_preference_collecting():
    split_result, route_result = await _split_and_route("tôi nên đăng ký lớp nào kỳ sau")
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "class_registration_suggestion"

    response = await _process_single_query(
        normalized_text="toi nen dang ky lop nao ky sau",
        student_id=1,
        conversation_id=11,
        db=_NoDbExecute(),
        chatbot_service=_FakeChatbotService(),
        forced_intent="class_registration_suggestion",
    )
    assert response.intent == "class_registration_suggestion"
    assert getattr(response.metadata, "question_type", None) == "single_choice"
    assert getattr(response.metadata, "is_preference_collecting", None) is True


@pytest.mark.asyncio
async def test_case_7_class_registration_with_days_stays_single_segment():
    split_result, route_result = await _split_and_route(
        "tôi nên đăng ký lớp nào kỳ sau, tôi muốn học thứ 2, thứ 3, thứ 4"
    )
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "class_registration_suggestion"
    assert set(route_result["constraints"].get("days", [])) >= {"Monday", "Tuesday", "Wednesday"}


@pytest.mark.asyncio
async def test_case_8_subject_registration_excludes_jp3110():
    split_result, route_result = await _split_and_route(
        "tôi nên đăng ký học phần nào kỳ sau, tôi không muốn học môn JP3110"
    )
    assert len(split_result["segments"]) == 1
    assert route_result["intent"] == "subject_registration_suggestion"
    assert "jp3110" in route_result["constraints"].get("exclude_subjects", [])
    assert route_result["constraints"].get("preferred_subjects", []) == []
