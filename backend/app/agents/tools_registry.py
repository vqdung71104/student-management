import json
import os
import time
from typing import Any, Dict, List, Optional

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


def _classify_error(exc: Exception) -> str:
    """
    Classify an HTTP/client exception into a clear, actionable error category.
    Used by both tools_registry (log) and orchestrator (capture).
    """
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 403:
            return f"HTTP_403_AUTH: X-Agent-Internal-Key missing or wrong on {exc.request.url}"
        if status == 401:
            return f"HTTP_401_UNAUTHORIZED: Invalid credentials on {exc.request.url}"
        if status == 404:
            return f"HTTP_404_NOT_FOUND: Endpoint not found {exc.request.url}"
        if status == 422:
            return f"HTTP_422_VALIDATION: Request body invalid for {exc.request.url}"
        return f"HTTP_{status}: {exc.response.text[:120]} on {exc.request.url}"
    if isinstance(exc, httpx.TimeoutException):
        return f"TIMEOUT: Request timed out"
    if isinstance(exc, httpx.ConnectError):
        return f"CONNECT_ERROR: Cannot reach server — is the backend running on {exc.request.url.host if hasattr(exc, 'request') else 'localhost'}?"
    if isinstance(exc, httpx.RemoteProtocolError):
        return f"REMOTE_PROTOCOL_ERROR: Server sent malformed response on {exc.request.url}"
    return f"UNKNOWN: {type(exc).__name__}: {exc}"

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

    async def call(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a registered tool endpoint.

        Returns a dict — never raises an exception:
          - On success:  {"status": "success", "data": {...}}
          - On HTTP error: {"status": "error", "error": "<classified reason>", "http_status": <int>}
          - On network error: {"status": "error", "error": "<classified reason>"}
        """
        tool = self.get(name)
        if not tool:
            raise RuntimeError(f"Tool {name} not found")
        url = tool["url"]
        timeout = tool.get("timeout", 5)
        custom_headers = (
            tool.get("headers", {})
            if isinstance(tool.get("headers"), dict)
            else {}
        )
        headers = {**self._default_headers, **custom_headers}
        payload_preview = json.dumps(payload, ensure_ascii=False, default=str)
        if len(payload_preview) > 160:
            payload_preview = payload_preview[:160] + "..."
        print(f"[TOOLS] start name={name} url={url} timeout={timeout}s payload={payload_preview}")
        started_at = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                resp = await client.post(url, json=payload)
                duration_ms = (time.perf_counter() - started_at) * 1000
                print(
                    f"[TOOLS] response name={name} status={resp.status_code} "
                    f"duration_ms={duration_ms:.1f}"
                )

                # ── Success ──────────────────────────────────────────────────────
                if resp.status_code == 200:
                    body = resp.json()
                    body_preview = json.dumps(body, ensure_ascii=False, default=str)
                    if len(body_preview) > 160:
                        body_preview = body_preview[:160] + "..."
                    print(f"[TOOLS] done name={name} body={body_preview}")
                    return body  # passthrough so orchestrator sees real data

                # ── HTTP error — return structured error, do NOT raise ─────────────
                err_category = _classify_error(
                    httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                )
                err_detail = (
                    resp.text[:200].strip() if resp.text else f"HTTP {resp.status_code}"
                )
                print(
                    f"[TOOLS] HTTP error name={name} status={resp.status_code} "
                    f"category={err_category} detail={err_detail[:80]}"
                )
                return {
                    "status": "error",
                    "error": err_category,
                    "http_status": resp.status_code,
                    "error_detail": err_detail,
                }

        except httpx.TimeoutException as exc:
            duration_ms = (time.perf_counter() - started_at) * 1000
            err = _classify_error(exc)
            print(f"[TOOLS] timeout name={name} duration_ms={duration_ms:.1f} error={err}")
            return {"status": "error", "error": err}

        except httpx.ConnectError as exc:
            duration_ms = (time.perf_counter() - started_at) * 1000
            err = _classify_error(exc)
            print(f"[TOOLS] connect_error name={name} duration_ms={duration_ms:.1f} error={err}")
            return {"status": "error", "error": err}

        except httpx.HTTPStatusError as exc:
            # Already handled above via status_code check, but kept as fallback
            err = _classify_error(exc)
            return {"status": "error", "error": err}

        except Exception as exc:
            duration_ms = (time.perf_counter() - started_at) * 1000
            err_category = _classify_error(exc)
            print(
                f"[TOOLS] unexpected name={name} duration_ms={duration_ms:.1f} "
                f"error={err_category}"
            )
            return {"status": "error", "error": err_category}
