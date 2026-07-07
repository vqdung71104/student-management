"""
End-to-end chatbot trace test.

This test intentionally exercises the real chatbot endpoint and records a
human-readable trace for thesis/demo review. It does not change application
logic; it only wraps existing services during the test run so inputs, outputs,
scores, SQL, preferences, and schedule-combination reasoning are persisted.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Keep the app startup stable. The LLM scenario enables AGENT_ENABLED only for
# that request and then restores it.
ORIGINAL_AGENT_ENABLED = os.environ.get("AGENT_ENABLED")
os.environ["AGENT_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text as sql_text  # noqa: E402

from app.chatbot.tfidf_classifier import TfidfIntentClassifier  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.database import SessionLocal, get_db  # noqa: E402
from app.models.student_model import Student  # noqa: E402
from app.services.chatbot_service import ChatbotService  # noqa: E402
from app.services.class_query_service import ClassQueryService  # noqa: E402
from app.services.nl2sql_service import NL2SQLService  # noqa: E402
from app.services.preference_service import PreferenceCollectionService  # noqa: E402
from app.services.schedule_combination_service import ScheduleCombinationGenerator  # noqa: E402
from app.utils.jwt_utils import get_current_student, get_current_user  # noqa: E402
from main import app  # noqa: E402


OUTPUT_DIR = BACKEND_DIR / "outputs" / "chatbot_e2e_trace"
REPORT_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_REPORT = OUTPUT_DIR / f"run_{REPORT_TS}.json"
MD_REPORT = OUTPUT_DIR / f"run_{REPORT_TS}.md"


def _jsonable(value: Any) -> Any:
    """Convert Pydantic/SQLAlchemy/datetime-ish values into JSON-safe data."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "__dict__") and value.__class__.__module__.startswith("app.models"):
        return {
            key: _jsonable(val)
            for key, val in value.__dict__.items()
            if not key.startswith("_")
        }
    return str(value)


def _truncate(value: Any, limit: int = 4000) -> Any:
    value = _jsonable(value)
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"... <truncated {len(value) - limit} chars>"
    if isinstance(value, list):
        return [_truncate(item, limit) for item in value[:20]]
    if isinstance(value, dict):
        return {key: _truncate(val, limit) for key, val in value.items()}
    return value


def _mask_db_url(url: str) -> str:
    if "://" not in url or "@" not in url:
        return url
    prefix, rest = url.split("://", 1)
    auth, host = rest.split("@", 1)
    user = auth.split(":", 1)[0]
    return f"{prefix}://{user}:***@{host}"


class TraceRecorder:
    def __init__(self) -> None:
        self.active_scenario: Optional[str] = None
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.events: List[Dict[str, Any]] = []

    def start(self, scenario_id: str, title: str, message: str) -> None:
        self.active_scenario = scenario_id
        self.scenarios[scenario_id] = {
            "id": scenario_id,
            "title": title,
            "messages": [message],
            "events": [],
            "responses": [],
            "stdout": [],
            "status": "running",
        }

    def append_message(self, scenario_id: str, message: str) -> None:
        self.scenarios[scenario_id]["messages"].append(message)

    def finish(self, scenario_id: str, status: str = "passed", error: Optional[str] = None) -> None:
        self.scenarios[scenario_id]["status"] = status
        if error:
            self.scenarios[scenario_id]["error"] = error
        self.active_scenario = None

    def log(self, event: str, **payload: Any) -> None:
        scenario_id = self.active_scenario or "global"
        item = {
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "scenario_id": scenario_id,
            "event": event,
            "payload": _truncate(payload),
        }
        self.events.append(item)
        if scenario_id in self.scenarios:
            self.scenarios[scenario_id]["events"].append(item)

    def add_response(self, scenario_id: str, response: Any) -> None:
        self.scenarios[scenario_id]["responses"].append(_truncate(response))

    def add_stdout(self, scenario_id: str, stdout_text: str) -> None:
        lines = [line for line in stdout_text.splitlines() if line.strip()]
        self.scenarios[scenario_id]["stdout"].extend(lines[-300:])


def _timed_call(recorder: TraceRecorder, event: str, fn: Callable, *args: Any, **kwargs: Any) -> Any:
    started = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
        recorder.log(event, input={"args": args, "kwargs": kwargs}, output=result, duration_ms=(time.perf_counter() - started) * 1000)
        return result
    except Exception as exc:
        recorder.log(event, input={"args": args, "kwargs": kwargs}, error=f"{type(exc).__name__}: {exc}", duration_ms=(time.perf_counter() - started) * 1000)
        raise


def install_trace_wrappers(monkeypatch: pytest.MonkeyPatch, recorder: TraceRecorder) -> None:
    from app.routes import chatbot_routes
    from app.services import query_splitter as query_splitter_module

    original_preprocess = chatbot_routes.text_preprocessor.preprocess

    def preprocess_wrapper(text: str) -> str:
        return _timed_call(recorder, "text_preprocessor.preprocess", original_preprocess, text)

    monkeypatch.setattr(chatbot_routes.text_preprocessor, "preprocess", preprocess_wrapper)

    original_split = chatbot_routes.query_splitter.split

    def split_wrapper(text: str):
        result = _timed_call(recorder, "query_splitter.split", original_split, text)
        recorder.log(
            "query_splitter.result",
            segments=[
                {
                    "text": getattr(segment, "text", None),
                    "detected_intent": getattr(segment, "detected_intent", None),
                    "intent_score": getattr(segment, "intent_score", None),
                }
                for segment in result
            ],
        )
        return result

    monkeypatch.setattr(chatbot_routes.query_splitter, "split", split_wrapper)

    original_score_intents = query_splitter_module.QuerySplitter._score_intents

    def score_intents_wrapper(self, lower_text: str):
        result = original_score_intents(self, lower_text)
        recorder.log("query_splitter.marker_scores", text=lower_text, scores=result)
        return result

    monkeypatch.setattr(query_splitter_module.QuerySplitter, "_score_intents", score_intents_wrapper)

    original_classify = TfidfIntentClassifier.classify_intent

    async def classify_wrapper(self, message: str):
        started = time.perf_counter()
        try:
            result = await original_classify(self, message)
            recorder.log(
                "intent_classifier.classify_intent",
                message=message,
                intent=result.get("intent"),
                confidence=result.get("confidence"),
                confidence_score=result.get("confidence_score"),
                method=result.get("method"),
                tfidf_score=result.get("tfidf_score"),
                semantic_score=result.get("semantic_score"),
                keyword_score=result.get("keyword_score"),
                exact_bonus=result.get("exact_bonus"),
                boost_applied=result.get("boost_applied"),
                boost_reasons=result.get("boost_reasons"),
                adaptive_weights=result.get("adaptive_weights"),
                margin=result.get("margin"),
                all_scores=result.get("all_scores"),
                duration_ms=(time.perf_counter() - started) * 1000,
            )
            return result
        except Exception as exc:
            recorder.log("intent_classifier.classify_intent.error", message=message, error=f"{type(exc).__name__}: {exc}")
            raise

    monkeypatch.setattr(TfidfIntentClassifier, "classify_intent", classify_wrapper)

    original_generate_sql = NL2SQLService.generate_sql

    async def generate_sql_wrapper(self, question: str, intent: str, student_id: Optional[int] = None, db=None):
        started = time.perf_counter()
        result = await original_generate_sql(self, question=question, intent=intent, student_id=student_id, db=db)
        recorder.log(
            "nl2sql.generate_sql",
            question=question,
            intent=intent,
            student_id=student_id,
            entities=result.get("entities"),
            template_match=result.get("template_match"),
            method=result.get("method"),
            sql=result.get("sql"),
            error=result.get("error"),
            fuzzy_match=result.get("fuzzy_match"),
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return result

    monkeypatch.setattr(NL2SQLService, "generate_sql", generate_sql_wrapper)

    def wrap_async_service(method_name: str) -> None:
        original = getattr(ChatbotService, method_name)

        async def wrapper(self, *args, **kwargs):
            started = time.perf_counter()
            try:
                result = await original(self, *args, **kwargs)
                recorder.log(
                    f"chatbot_service.{method_name}",
                    input={"args": args, "kwargs": kwargs},
                    output=result,
                    duration_ms=(time.perf_counter() - started) * 1000,
                )
                return result
            except Exception as exc:
                recorder.log(f"chatbot_service.{method_name}.error", input={"args": args, "kwargs": kwargs}, error=f"{type(exc).__name__}: {exc}")
                raise

        monkeypatch.setattr(ChatbotService, method_name, wrapper)

    for name in (
        "process_subject_suggestion",
        "process_class_suggestion",
        "process_modify_schedule",
        "_generate_class_suggestions_with_preferences",
    ):
        wrap_async_service(name)

    original_process_class_info = ChatbotService.process_class_info

    async def process_class_info_wrapper(self, *args, **kwargs):
        started = time.perf_counter()
        result = await original_process_class_info(self, *args, **kwargs)
        forced_output = None if recorder.active_scenario == "orm_class_query" else result
        recorder.log(
            "chatbot_service.process_class_info",
            input={"args": args, "kwargs": kwargs},
            output=result,
            forced_output=forced_output,
            note=(
                "orm_class_query forces direct class_info fallback so the route can exercise "
                "ConstraintExtractor + ClassQueryService.query."
                if recorder.active_scenario == "orm_class_query"
                else None
            ),
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return forced_output

    monkeypatch.setattr(ChatbotService, "process_class_info", process_class_info_wrapper)

    original_extract_initial = PreferenceCollectionService.extract_initial_preferences

    def extract_initial_wrapper(self, question: str):
        result = original_extract_initial(self, question)
        recorder.log("preference.extract_initial_preferences", question=question, preferences=result.dict(), missing=result.get_missing_preferences(), complete=result.is_complete())
        return result

    monkeypatch.setattr(PreferenceCollectionService, "extract_initial_preferences", extract_initial_wrapper)

    original_parse_response = PreferenceCollectionService.parse_user_response

    def parse_response_wrapper(self, response: str, question_key: str, current_preferences):
        before = deepcopy(current_preferences.dict())
        result = original_parse_response(self, response, question_key, current_preferences)
        recorder.log(
            "preference.parse_user_response",
            response=response,
            question_key=question_key,
            before=before,
            after=result.dict(),
            missing=result.get_missing_preferences(),
            complete=result.is_complete(),
        )
        return result

    monkeypatch.setattr(PreferenceCollectionService, "parse_user_response", parse_response_wrapper)

    original_get_next_question = PreferenceCollectionService.get_next_question

    def get_next_question_wrapper(self, preferences):
        result = original_get_next_question(self, preferences)
        recorder.log(
            "preference.get_next_question",
            preferences=preferences.dict(),
            missing=preferences.get_missing_preferences(),
            next_question=result.dict() if result else None,
        )
        return result

    monkeypatch.setattr(PreferenceCollectionService, "get_next_question", get_next_question_wrapper)

    original_class_query = ClassQueryService.query

    def class_query_wrapper(self, constraints, include_full: bool = False):
        started = time.perf_counter()
        result = original_class_query(self, constraints, include_full=include_full)
        recorder.log(
            "class_query_service.query",
            constraints=constraints.dict() if hasattr(constraints, "dict") else constraints,
            include_full=include_full,
            row_count=len(result) if isinstance(result, list) else None,
            sample=result[:5] if isinstance(result, list) else result,
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return result

    monkeypatch.setattr(ClassQueryService, "query", class_query_wrapper)

    original_generate_combinations = ScheduleCombinationGenerator.generate_combinations

    def generate_combinations_wrapper(self, classes_by_subject: Dict[str, List[Dict]], preferences: Dict, max_combinations: int = 100):
        started = time.perf_counter()
        result = original_generate_combinations(self, classes_by_subject, preferences, max_combinations=max_combinations)
        recorder.log(
            "schedule_combination.generate_combinations",
            subject_count=len(classes_by_subject),
            candidate_counts={key: len(value or []) for key, value in classes_by_subject.items()},
            preferences=preferences,
            max_combinations=max_combinations,
            combination_count=len(result),
            top_scores=[item.get("score") for item in result[:5]],
            top_samples=result[:3],
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return result

    monkeypatch.setattr(ScheduleCombinationGenerator, "generate_combinations", generate_combinations_wrapper)

    original_score = ScheduleCombinationGenerator.calculate_combination_score

    def score_wrapper(self, classes: List[Dict], preferences: Dict):
        result = original_score(self, classes, preferences)
        recorder.log(
            "schedule_combination.calculate_combination_score",
            class_ids=[cls.get("class_id") for cls in classes],
            subject_ids=[cls.get("subject_id") for cls in classes],
            preferences=preferences,
            score=result,
        )
        return result

    monkeypatch.setattr(ScheduleCombinationGenerator, "calculate_combination_score", score_wrapper)

    from app.agents.agent_orchestrator import AgentOrchestrator

    original_agent_handle = AgentOrchestrator.handle

    async def agent_handle_wrapper(self, user_text: str, student_id: Optional[int] = None, conversation_id: Optional[int] = None):
        started = time.perf_counter()
        try:
            result = await original_agent_handle(self, user_text, student_id=student_id, conversation_id=conversation_id)
            recorder.log(
                "agent_orchestrator.handle",
                user_text=user_text,
                student_id=student_id,
                conversation_id=conversation_id,
                intent=result.get("intent") if isinstance(result, dict) else None,
                debug=result.get("debug") if isinstance(result, dict) else None,
                raw=result.get("raw") if isinstance(result, dict) else None,
                response=result.get("response") if isinstance(result, dict) else result,
                duration_ms=(time.perf_counter() - started) * 1000,
            )
            return result
        except Exception as exc:
            recorder.log("agent_orchestrator.handle.error", user_text=user_text, error=f"{type(exc).__name__}: {exc}", duration_ms=(time.perf_counter() - started) * 1000)
            raise

    monkeypatch.setattr(AgentOrchestrator, "handle", agent_handle_wrapper)


def _pick_student() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        student = db.query(Student).order_by(Student.id.asc()).first()
        if not student:
            raise AssertionError("Không tìm thấy student thật trong DB. Hãy seed dữ liệu trước khi chạy E2E trace test.")
        return {"id": student.id, "student_name": student.student_name, "email": student.email, "course_id": student.course_id}
    finally:
        db.close()


def _collect_data_fixtures(student_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        subjects = db.execute(
            sql_text(
                """
                SELECT subject_id, subject_name
                FROM subjects
                WHERE subject_name LIKE :name OR subject_id IN ('IT2030', 'IT3080', 'EM1180Q')
                ORDER BY subject_id
                LIMIT 20
                """
            ),
            {"name": "%Cấu trúc dữ liệu%"},
        ).mappings().all()
        classes = db.execute(
            sql_text(
                """
                SELECT c.class_id, c.classroom, c.study_date, s.subject_id, s.subject_name
                FROM classes c
                JOIN subjects s ON c.subject_id = s.id
                ORDER BY c.id
                LIMIT 20
                """
            )
        ).mappings().all()
        registered = db.execute(
            sql_text(
                """
                SELECT c.class_id, s.subject_id, s.subject_name
                FROM class_registers cr
                JOIN classes c ON cr.class_id = c.id
                JOIN subjects s ON c.subject_id = s.id
                WHERE cr.student_id = :student_id
                LIMIT 20
                """
            ),
            {"student_id": student_id},
        ).mappings().all()
        return {
            "subjects": [dict(row) for row in subjects],
            "classes": [dict(row) for row in classes],
            "registered_classes": [dict(row) for row in registered],
        }
    finally:
        db.close()


def _post_chat(client: TestClient, recorder: TraceRecorder, scenario_id: str, message: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"message": message}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        response = client.post("/api/chatbot/chat", json=payload)
    recorder.add_stdout(scenario_id, stdout.getvalue())

    body: Any
    try:
        body = response.json()
    except Exception:
        body = {"raw_text": response.text}

    recorder.log("http.response", status_code=response.status_code, request_payload=payload, response=body)
    recorder.add_response(scenario_id, body)
    assert response.status_code == 200, f"{scenario_id} failed HTTP {response.status_code}: {body}"
    return body


def _make_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Chatbot E2E Trace Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Student: `{report['student'].get('id')}` - {report['student'].get('student_name')}",
        f"- Agent enabled original env: `{report['environment'].get('original_agent_enabled')}`",
        f"- OpenAI model: `{report['environment'].get('openai_model')}`",
        f"- Summary: `{report['summary']['passed']}/{report['summary']['total']}` passed",
        "",
        "## Data Fixtures",
        "",
        "```json",
        json.dumps(report["fixtures"], ensure_ascii=False, indent=2, default=str)[:6000],
        "```",
        "",
    ]

    for scenario in report["scenarios"]:
        lines.extend(
            [
                f"## {scenario['title']}",
                "",
                f"- Scenario id: `{scenario['id']}`",
                f"- Status: `{scenario['status']}`",
                f"- Messages: {', '.join(f'`{m}`' for m in scenario.get('messages', []))}",
                "",
                "### Final Responses",
                "",
            ]
        )
        for idx, response in enumerate(scenario.get("responses", []), start=1):
            debug = response.get("debug") if isinstance(response, dict) else None
            data = response.get("data") or [] if isinstance(response, dict) else []
            data_keys = sorted(data[0].keys()) if data and isinstance(data[0], dict) else []
            lines.extend(
                [
                    f"#### Response {idx}",
                    "",
                    f"- Intent: `{response.get('intent') if isinstance(response, dict) else None}`",
                    f"- Confidence: `{response.get('confidence') if isinstance(response, dict) else None}`",
                    f"- Route/debug: `{debug}`",
                    f"- SQL: `{response.get('sql') if isinstance(response, dict) else None}`",
                    f"- SQL error: `{response.get('sql_error') if isinstance(response, dict) else None}`",
                    f"- Data count: `{len(response.get('data') or []) if isinstance(response, dict) else 0}`",
                    f"- First data keys: `{data_keys}`",
                    "",
                    "Text preview:",
                    "",
                    "```text",
                    str(response.get("text", ""))[:2500] if isinstance(response, dict) else str(response)[:2500],
                    "```",
                    "",
                ]
            )

        interesting_events = [
            event
            for event in scenario.get("events", [])
            if event["event"]
            in {
                "query_splitter.result",
                "query_splitter.marker_scores",
                "intent_classifier.classify_intent",
                "nl2sql.generate_sql",
                "preference.extract_initial_preferences",
                "preference.parse_user_response",
                "preference.get_next_question",
                "class_query_service.query",
                "schedule_combination.generate_combinations",
                "schedule_combination.calculate_combination_score",
                "chatbot_service.process_class_info",
                "chatbot_service.process_subject_suggestion",
                "chatbot_service.process_class_suggestion",
                "chatbot_service.process_modify_schedule",
                "agent_orchestrator.handle",
            }
        ]
        lines.extend(["### Step Trace", "", "```json"])
        lines.append(json.dumps(interesting_events, ensure_ascii=False, indent=2, default=str)[:40000])
        lines.extend(["```", ""])

        if scenario.get("stdout"):
            lines.extend(["### Raw Logs", "", "```text"])
            lines.append("\n".join(scenario["stdout"][-120:])[:20000])
            lines.extend(["```", ""])

    return "\n".join(lines)


def _write_reports(recorder: TraceRecorder, student: Dict[str, Any], fixtures: Dict[str, Any], failures: List[str]) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = list(recorder.scenarios.values())
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "environment": {
            "database_url": _mask_db_url(settings.DATABASE_URL),
            "original_agent_enabled": ORIGINAL_AGENT_ENABLED,
            "agent_enabled_at_end": os.environ.get("AGENT_ENABLED"),
            "openai_model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "has_openai_api_key": bool(os.environ.get("OPENAI_API_KEY")),
            "llm_timeouts": {
                "LLM_SPLIT_TIMEOUT": os.environ.get("LLM_SPLIT_TIMEOUT"),
                "LLM_CLASSIFY_TIMEOUT": os.environ.get("LLM_CLASSIFY_TIMEOUT"),
                "LLM_GENERATE_TIMEOUT": os.environ.get("LLM_GENERATE_TIMEOUT"),
            },
        },
        "student": student,
        "fixtures": fixtures,
        "scenarios": scenarios,
        "events": recorder.events,
        "summary": {
            "total": len(scenarios),
            "passed": sum(1 for item in scenarios if item.get("status") == "passed"),
            "failed": sum(1 for item in scenarios if item.get("status") != "passed"),
            "failures": failures,
            "json_report": str(JSON_REPORT),
            "markdown_report": str(MD_REPORT),
        },
    }
    JSON_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    MD_REPORT.write_text(_make_markdown(report), encoding="utf-8")
    return report


def _assert_branch_coverage(report: Dict[str, Any]) -> None:
    all_events = report["events"]
    event_names = [event["event"] for event in all_events]
    scenarios_by_id = {item["id"]: item for item in report["scenarios"]}

    assert JSON_REPORT.exists(), f"JSON report was not written: {JSON_REPORT}"
    assert MD_REPORT.exists(), f"Markdown report was not written: {MD_REPORT}"
    assert all(item.get("events") for item in report["scenarios"]), "Mỗi scenario cần có trace events."

    no_split = scenarios_by_id["and_in_subject_name"]
    split_events = [event for event in no_split["events"] if event["event"] == "query_splitter.result"]
    assert split_events, "Thiếu trace splitter cho case tên môn có chữ 'và'."
    first_segments = split_events[0]["payload"].get("segments") or []
    assert len(first_segments) == 1, "Không được split chữ 'và' trong tên môn Cấu trúc dữ liệu và giải thuật."

    multi = scenarios_by_id["multi_intent"]
    multi_response = multi["responses"][-1]
    assert multi_response.get("is_compound") or len(multi_response.get("parts") or []) > 1, "Multi-intent phải tạo compound response hoặc parts > 1."

    class_scenario = scenarios_by_id["class_registration_multiturn"]
    class_final = class_scenario["responses"][-1]
    class_data = class_final.get("data") or []
    class_event_names = [event["event"] for event in class_scenario["events"]]
    class_metadata = class_final.get("metadata") or {}
    result_metadata = class_metadata.get("result") if isinstance(class_metadata, dict) else None
    conversation_metadata = class_metadata.get("conversation") if isinstance(class_metadata, dict) else None

    assert "chatbot_service.process_class_suggestion" in class_event_names, "Thiếu nhánh class suggestion."
    assert "preference.extract_initial_preferences" in class_event_names, "Thiếu trace lấy preference ban đầu."
    assert "preference.parse_user_response" in class_event_names, "Thiếu trace parse câu trả lời preference."
    assert "preference.get_next_question" in class_event_names, "Thiếu trace chọn câu hỏi preference kế tiếp."

    has_response_combination_reasoning = any(
        isinstance(item, dict) and ("score" in item or "reasoning" in item or "combination_id" in item)
        for item in class_data
    )
    has_schedule_reasoning_trace = any(
        event_name in class_event_names
        for event_name in (
            "schedule_combination.generate_combinations",
            "schedule_combination.calculate_combination_score",
            "chatbot_service._generate_class_suggestions_with_preferences",
        )
    )
    no_combination_result = (
        isinstance(result_metadata, dict) and result_metadata.get("total_combinations") == 0
    ) or (
        isinstance(class_metadata, dict) and class_metadata.get("total_combinations") == 0
    )
    still_collecting_preferences = isinstance(conversation_metadata, dict) and conversation_metadata.get("stage") in {
        "collecting",
        "collecting_preferences",
    }
    assert (
        has_response_combination_reasoning
        or has_schedule_reasoning_trace
        or no_combination_result
        or still_collecting_preferences
    ), (
        "Class suggestion trace phải có reasoning thật từ response, trace generate/score tổ hợp, "
        "hoặc metadata cho biết hệ thống chưa/không tạo được tổ hợp."
    )

    nl2sql = scenarios_by_id["nl2sql_schedule"]["responses"][-1]
    assert nl2sql.get("sql") or nl2sql.get("sql_error") or any(event["event"] == "nl2sql.generate_sql" for event in scenarios_by_id["nl2sql_schedule"]["events"]), "NL2SQL scenario phải ghi SQL hoặc lỗi SQL."

    assert "chatbot_service.process_subject_suggestion" in event_names, "Thiếu nhánh subject suggestion."
    assert "chatbot_service.process_modify_schedule" in event_names, "Thiếu nhánh modify schedule."
    assert "class_query_service.query" in event_names, "Thiếu nhánh ORM ClassQueryService."

    llm = scenarios_by_id["real_llm_agent"]["responses"][-1]
    debug = llm.get("debug") or {}
    assert debug.get("llm_called") is True or any(event["event"] == "agent_orchestrator.handle" for event in scenarios_by_id["real_llm_agent"]["events"]), "Real LLM scenario phải đi qua agent/LLM."


def test_chatbot_e2e_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = TraceRecorder()
    failures: List[str] = []
    student = _pick_student()
    fixtures = _collect_data_fixtures(student["id"])

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        db = SessionLocal()
        try:
            return db.query(Student).filter(Student.id == student["id"]).first()
        finally:
            db.close()

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_student] = override_current_user

    install_trace_wrappers(monkeypatch, recorder)
    from app.routes import chatbot_routes
    from app.services import conversation_state as conversation_state_module

    memory_conversation_manager = conversation_state_module.get_conversation_manager()
    memory_conversation_manager._states.clear()
    monkeypatch.setattr(conversation_state_module, "get_conversation_state_manager", lambda: memory_conversation_manager)
    monkeypatch.setattr(chatbot_routes, "get_conversation_state_manager", lambda: memory_conversation_manager)

    scenarios = [
        ("greeting_legacy", "Single intent không cần LLM", "xin chào"),
        ("multi_intent", "Multi intent qua query splitter", "xem cpa và lịch học của tôi"),
        ("and_in_subject_name", "Không split chữ và trong tên môn", "thông tin học phần Cấu trúc dữ liệu và giải thuật"),
        ("subject_registration", "Gợi ý đăng ký học phần", "kỳ sau tôi nên đăng ký học phần gì"),
        ("modify_schedule", "Điều chỉnh thời khóa biểu", "kiểm tra tkb và đề xuất bỏ lớp hoặc đăng ký thêm"),
        ("orm_class_query", "ORM ClassQueryService path", "các lớp học sáng thứ 2"),
        ("nl2sql_schedule", "NL2SQL schedule path", "lịch học của tôi"),
    ]

    try:
        with TestClient(app) as client:
            for scenario_id, title, message in scenarios:
                recorder.start(scenario_id, title, message)
                os.environ["AGENT_ENABLED"] = "false"
                try:
                    body = _post_chat(client, recorder, scenario_id, message)
                    if scenario_id == "greeting_legacy":
                        assert body.get("debug", {}).get("llm_called") is False
                    recorder.finish(scenario_id)
                except Exception as exc:
                    failures.append(f"{scenario_id}: {type(exc).__name__}: {exc}")
                    recorder.finish(scenario_id, status="failed", error=f"{type(exc).__name__}: {exc}")

            scenario_id = "class_registration_multiturn"
            class_messages = [
                "tôi nên đăng ký lớp nào kỳ sau",
                "Thứ 2, Thứ 4, Thứ 6",
                "1",
                "2",
                "1",
                "không có yêu cầu gì thêm",
            ]
            recorder.start(scenario_id, "Gợi ý đăng ký lớp multi-turn và preference", class_messages[0])
            os.environ["AGENT_ENABLED"] = "false"
            try:
                conversation_id = None
                for idx, message in enumerate(class_messages):
                    if idx > 0:
                        recorder.append_message(scenario_id, message)
                    body = _post_chat(client, recorder, scenario_id, message, conversation_id=conversation_id)
                    conversation_id = body.get("conversation_id") or conversation_id
                recorder.finish(scenario_id)
            except Exception as exc:
                failures.append(f"{scenario_id}: {type(exc).__name__}: {exc}")
                recorder.finish(scenario_id, status="failed", error=f"{type(exc).__name__}: {exc}")

            scenario_id = "real_llm_agent"
            message = "xem cpa, sau đó gợi ý học phần kỳ sau nhưng tránh môn JP3110"
            recorder.start(scenario_id, "Real LLM agent path", message)
            try:
                if not os.environ.get("OPENAI_API_KEY"):
                    raise AssertionError(
                        "OPENAI_API_KEY is required for the real LLM scenario. "
                        "Set OPENAI_API_KEY and rerun pytest backend/tests/test_chatbot_e2e_trace.py -s"
                    )
                os.environ["AGENT_ENABLED"] = "true"
                body = _post_chat(client, recorder, scenario_id, message)
                assert body.get("debug", {}).get("llm_called") is True, body.get("debug")
                recorder.finish(scenario_id)
            except Exception as exc:
                failures.append(f"{scenario_id}: {type(exc).__name__}: {exc}")
                recorder.finish(scenario_id, status="failed", error=f"{type(exc).__name__}: {exc}")
            finally:
                os.environ["AGENT_ENABLED"] = "false"
    finally:
        if ORIGINAL_AGENT_ENABLED is None:
            os.environ.pop("AGENT_ENABLED", None)
        else:
            os.environ["AGENT_ENABLED"] = ORIGINAL_AGENT_ENABLED
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        report = _write_reports(recorder, student, fixtures, failures)

    _assert_branch_coverage(report)
    assert not failures, "E2E trace failures:\n" + "\n".join(failures)
