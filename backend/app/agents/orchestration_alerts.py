import os
from typing import Any, Dict, List


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


ALERT_WINDOW_NOTE = "Thresholds are evaluated against current in-memory counters since process start."

ALERT_LLM_TIMEOUT_MIN = float(os.getenv("ALERT_LLM_TIMEOUT_MIN", "5"))
ALERT_NODE4_FALLBACK_MIN = float(os.getenv("ALERT_NODE4_FALLBACK_MIN", "5"))
ALERT_TOOLS_FAILURE_MIN = float(os.getenv("ALERT_TOOLS_FAILURE_MIN", "5"))
ALERT_CIRCUIT_OPEN_MIN = float(os.getenv("ALERT_CIRCUIT_OPEN_MIN", "3"))


def evaluate_orchestration_alerts(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    counters = snapshot.get("counters", {}) if isinstance(snapshot, dict) else {}

    llm_timeout_failures = 0.0
    llm_circuit_open = 0.0
    tools_failures = 0.0

    for key, value in counters.items():
        numeric = _to_float(value)
        if key.startswith("llm.") and key.endswith(".failure"):
            llm_timeout_failures += numeric
        if key.startswith("llm.") and key.endswith(".circuit_open"):
            llm_circuit_open += numeric
        if key.startswith("tools.") and key.endswith(".failure"):
            tools_failures += numeric

    node4_fallback = _to_float(counters.get("node4.fallback", 0.0))

    active_alerts: List[Dict[str, Any]] = []

    if llm_timeout_failures >= ALERT_LLM_TIMEOUT_MIN:
        active_alerts.append(
            {
                "code": "llm_timeout_spike",
                "severity": "warning",
                "value": llm_timeout_failures,
                "threshold": ALERT_LLM_TIMEOUT_MIN,
                "message": "LLM failures are above threshold.",
            }
        )

    if node4_fallback >= ALERT_NODE4_FALLBACK_MIN:
        active_alerts.append(
            {
                "code": "node4_fallback_spike",
                "severity": "warning",
                "value": node4_fallback,
                "threshold": ALERT_NODE4_FALLBACK_MIN,
                "message": "Node-4 fallback count is above threshold.",
            }
        )

    if tools_failures >= ALERT_TOOLS_FAILURE_MIN:
        active_alerts.append(
            {
                "code": "tools_failure_spike",
                "severity": "critical",
                "value": tools_failures,
                "threshold": ALERT_TOOLS_FAILURE_MIN,
                "message": "Tool invocation failures are above threshold.",
            }
        )

    if llm_circuit_open >= ALERT_CIRCUIT_OPEN_MIN:
        active_alerts.append(
            {
                "code": "llm_circuit_open_persistent",
                "severity": "critical",
                "value": llm_circuit_open,
                "threshold": ALERT_CIRCUIT_OPEN_MIN,
                "message": "LLM circuit has opened repeatedly.",
            }
        )

    return {
        "status": "alert" if active_alerts else "ok",
        "alerts": active_alerts,
        "summary": {
            "llm_failures": llm_timeout_failures,
            "node4_fallback": node4_fallback,
            "tools_failures": tools_failures,
            "llm_circuit_open": llm_circuit_open,
        },
        "note": ALERT_WINDOW_NOTE,
    }
