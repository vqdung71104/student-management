import sys
from pathlib import Path

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routes.chatbot_routes import (
    _fast_fallback_intent,
    _resolve_agent_routing,
    _should_auto_route_to_agent,
)


def test_fast_fallback_intent_subject_registration():
    text = "toi nen dang ky hoc phan nao ky sau, toi muon hoc mon MI1114"
    assert _fast_fallback_intent(text) == "subject_registration_suggestion"


def test_fast_fallback_intent_grade_view():
    assert _fast_fallback_intent("cpa cua toi la bao nhieu") == "grade_view"


def test_fast_fallback_intent_class_registration():
    text = "toi nen dang ky lop nao ky sau, toi muon hoc buoi sang"
    assert _fast_fallback_intent(text) == "class_registration_suggestion"


def test_auto_route_class_registration_with_preferences():
    text = "toi nen dang ky lop nao ky sau, toi khong thich hoc sang thu 2"
    assert _should_auto_route_to_agent(text) is True


def test_auto_route_class_registration_with_time_and_subject_preferences():
    text = "toi nen dang ky lop nao ky sau, toi khong thich hoc luc 6h45 va thich mon tieng nhat 6"
    assert _should_auto_route_to_agent(text) is True


def test_auto_route_keeps_plain_class_lookup_on_legacy():
    assert _should_auto_route_to_agent("cho toi xem cac lop mon IT3080") is False


def test_auto_route_keeps_grade_lookup_on_legacy():
    assert _should_auto_route_to_agent("xem diem cac mon truot") is False


def test_auto_route_subject_registration_compound_with_preferences():
    text = "em nen hoc mon gi nhung tranh sang thu 2 va xem luon diem may mon truot"
    assert _should_auto_route_to_agent(text) is True


def test_agent_route_disabled_stays_legacy(monkeypatch):
    monkeypatch.setenv("AGENT_ENABLED", "false")
    monkeypatch.setenv("AGENT_AUTO_ROUTE", "false")

    agent_enabled, auto_enabled, reason, auto_selected, use_agent = _resolve_agent_routing(
        "toi nen dang ky lop nao ky sau, toi khong thich hoc sang thu 2"
    )

    assert agent_enabled is False
    assert auto_enabled is False
    assert reason is None
    assert auto_selected is False
    assert use_agent is False


def test_agent_route_force_agent_wins(monkeypatch):
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("AGENT_AUTO_ROUTE", "false")

    agent_enabled, auto_enabled, reason, auto_selected, use_agent = _resolve_agent_routing(
        "xem diem cac mon truot"
    )

    assert agent_enabled is True
    assert auto_enabled is False
    assert reason is None
    assert auto_selected is False
    assert use_agent is True


def test_agent_route_auto_selects_complex_class_registration(monkeypatch):
    monkeypatch.setenv("AGENT_ENABLED", "false")
    monkeypatch.setenv("AGENT_AUTO_ROUTE", "true")

    agent_enabled, auto_enabled, reason, auto_selected, use_agent = _resolve_agent_routing(
        "toi nen dang ky lop nao ky sau, toi ko thich hoc sang thu 2 va thich mon tieng nhat 6"
    )

    assert agent_enabled is False
    assert auto_enabled is True
    assert reason == "class_registration_with_preferences"
    assert auto_selected is True
    assert use_agent is True


def test_agent_route_auto_keeps_simple_lookup_on_legacy(monkeypatch):
    monkeypatch.setenv("AGENT_ENABLED", "false")
    monkeypatch.setenv("AGENT_AUTO_ROUTE", "true")

    agent_enabled, auto_enabled, reason, auto_selected, use_agent = _resolve_agent_routing(
        "cho toi xem cac lop mon IT3080"
    )

    assert agent_enabled is False
    assert auto_enabled is True
    assert reason is None
    assert auto_selected is False
    assert use_agent is False
