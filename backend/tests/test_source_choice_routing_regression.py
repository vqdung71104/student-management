from app.services.chatbot_service import ChatbotService


def test_class_suggestion_subject_source_defaults_to_system_suggestions():
    normalizer = ChatbotService._normalize_subject_source_choice

    assert normalizer(None, None) == "suggested"
    assert normalizer(None, "suggested") == "suggested"
    assert not hasattr(ChatbotService, "_parse_subject_source_choice")
