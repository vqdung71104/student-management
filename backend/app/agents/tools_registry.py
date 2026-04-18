import json
import os
import time
from typing import Any, Dict, Optional

import httpx


DEFAULT_AGENT_TOOLS_BASE_URL = os.environ.get("AGENT_TOOLS_BASE_URL", "http://127.0.0.1:8000/api/agent-tools")
AGENT_INTERNAL_TOOL_KEY = os.environ.get("AGENT_INTERNAL_TOOL_KEY", "dev-agent-key")

DEFAULT_INTENT_TO_PATH = {
    "grade_view": "/intent/grade_view",
    "learned_subjects_view": "/intent/learned_subjects_view",
    "student_info": "/intent/student_info",
    "subject_info": "/intent/subject_info",
    "class_info": "/intent/class_info",
    "schedule_view": "/intent/schedule_view",
    "subject_registration_suggestion": "/intent/subject_registration_suggestion",
    "class_registration_suggestion": "/intent/class_registration_suggestion",
    "modify_schedule": "/intent/modify_schedule",
}


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _default_tool_map() -> Dict[str, Dict[str, Any]]:
    base_url = DEFAULT_AGENT_TOOLS_BASE_URL
    return {
        intent: {"url": _join_url(base_url, path), "timeout": 6}
        for intent, path in DEFAULT_INTENT_TO_PATH.items()
    }


def _load_tool_map_from_env() -> Dict[str, Dict[str, Any]]:
    raw = os.environ.get("AGENT_TOOLS_CONFIG_JSON", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid AGENT_TOOLS_CONFIG_JSON") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("AGENT_TOOLS_CONFIG_JSON must be a JSON object")

    normalized: Dict[str, Dict[str, Any]] = {}
    for name, cfg in parsed.items():
        if not isinstance(cfg, dict):
            continue
        url = cfg.get("url")
        timeout = cfg.get("timeout", 5)
        if isinstance(url, str) and url.strip():
            headers = cfg.get("headers") if isinstance(cfg.get("headers"), dict) else None
            normalized[str(name)] = {
                "url": url.strip(),
                "timeout": int(timeout),
                "headers": headers or {},
            }
    return normalized


AGENT_TOOL_MAP = _default_tool_map()
AGENT_TOOL_MAP.update(_load_tool_map_from_env())

class ToolsRegistry:
    def __init__(self, tool_map: Optional[Dict[str, Dict[str, Any]]] = None):
        self.tools = dict(tool_map) if tool_map is not None else dict(AGENT_TOOL_MAP)
        self._default_headers = {"X-Agent-Internal-Key": AGENT_INTERNAL_TOOL_KEY}

    def register(self, name: str, url: str, timeout: int = 5):
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not url or not isinstance(url, str):
            raise ValueError("Tool url must be a non-empty string")
        self.tools[name] = {"url": url, "timeout": timeout, "headers": {}}

    def get(self, name: str):
        return self.tools.get(name)

    async def call(self, name: str, payload: Dict[str, Any]):
        tool = self.get(name)
        if not tool:
            raise RuntimeError(f"Tool {name} not found")
        url = tool["url"]
        timeout = tool.get("timeout", 5)
        custom_headers = tool.get("headers", {}) if isinstance(tool.get("headers"), dict) else {}
        headers = {**self._default_headers, **custom_headers}
        payload_preview = json.dumps(payload, ensure_ascii=False, default=str)
        if len(payload_preview) > 160:
            payload_preview = payload_preview[:160] + "..."
        print(f"[TOOLS] start name={name} url={url} timeout={timeout}s payload={payload_preview}")
        started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            resp = await client.post(url, json=payload)
            duration_ms = (time.perf_counter() - started_at) * 1000
            print(f"[TOOLS] response name={name} status={resp.status_code} duration_ms={duration_ms:.1f}")
            resp.raise_for_status()
            body = resp.json()
            body_preview = json.dumps(body, ensure_ascii=False, default=str)
            if len(body_preview) > 160:
                body_preview = body_preview[:160] + "..."
            print(f"[TOOLS] done name={name} body={body_preview}")
            return body
