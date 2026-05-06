import sys
from pathlib import Path

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routes.chatbot_routes import _fast_fallback_intent


def test_fast_fallback_intent_subject_registration():
    text = "toi nen dang ky hoc phan nao ky sau, toi muon hoc mon MI1114"
    assert _fast_fallback_intent(text) == "subject_registration_suggestion"


def test_fast_fallback_intent_grade_view():
    assert _fast_fallback_intent("cpa cua toi la bao nhieu") == "grade_view"


def test_fast_fallback_intent_class_registration():
    text = "toi nen dang ky lop nao ky sau, toi muon hoc buoi sang"
    assert _fast_fallback_intent(text) == "class_registration_suggestion"
