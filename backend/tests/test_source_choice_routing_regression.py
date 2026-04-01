from app.services.chatbot_service import ChatbotService


def test_chatbot_source_choice_parser_handles_variants():
    parser = ChatbotService._parse_subject_source_choice
    # Call as unbound function since method is stateless
    assert parser(None, "hệ thống gợi ý") == "suggested"
    assert parser(None, "he thong goi y") == "suggested"
    assert parser(None, "đã đăng ký") == "registered"
    assert parser(None, "da dang ky") == "registered"
