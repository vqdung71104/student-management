import asyncio
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from app.agents.orchestration_metrics import get_orchestration_metrics

# ── Config ────────────────────────────────────────────────────────────────────
LLM_SPACE_URL = os.environ.get("LLM_SPACE_URL")
LLM_API_TOKEN = os.environ.get("LLM_API_TOKEN")

# Increased timeouts for reliability
LLM_CONNECT_TIMEOUT = float(os.environ.get("LLM_CONNECT_TIMEOUT", "10"))
LLM_DEFAULT_TIMEOUT = float(os.environ.get("LLM_DEFAULT_TIMEOUT", "120"))  # NEW: default 120s

LLM_SPLIT_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", os.environ.get("LLM_CLASSIFY_TIMEOUT", "2")))
LLM_CLASSIFY_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2"))
LLM_GENERATE_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "12"))  # NOTE: kept at 12s for generate as it's per-call timeout

LLM_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "48"))
LLM_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "12"))
LLM_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "160"))

LLM_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.2"))
LLM_FAST_TEMPERATURE = float(os.environ.get("LLM_FAST_TEMPERATURE", "0.0"))
LLM_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
LLM_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "1"))
LLM_RETRY_BASE_DELAY = float(os.environ.get("LLM_RETRY_BASE_DELAY", "0.2"))
LLM_BREAKER_FAIL_THRESHOLD = int(os.environ.get("LLM_BREAKER_FAIL_THRESHOLD", "5"))
LLM_BREAKER_COOLDOWN_SECONDS = float(os.environ.get("LLM_BREAKER_COOLDOWN_SECONDS", "30"))


# ── JSON Extraction Helper ─────────────────────────────────────────────────────

def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object/dict from raw text using regex, with logging on failure.

    Strategy:
    1. Try json.loads() directly first (fastest path for clean JSON).
    2. If that fails, use regex to find the first {...} block.
    3. If regex also fails, log the full raw_text for debugging and return None.

    This handles LLM responses that include extra text before/after the JSON block.

    Returns:
        Parsed dict if successful, None if all parsing attempts fail.
    """
    if not raw_text:
        return None

    # Path 1: Try direct parsing (clean JSON response)
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass  # Fall through to regex extraction

    # Path 2: Regex extraction - find first balanced {...} block
    # This regex matches from opening { to closing } with balanced nesting
    json_pattern = re.compile(r'\{(?:[^{}]|\{[^{}]*\})*\}', re.DOTALL)

    for match in json_pattern.finditer(raw_text):
        candidate = match.group(0)
        try:
            result = json.loads(candidate)
            print(f"[JSON_EXTRACT] regex_hit start={match.start()} end={match.end()} length={len(candidate)}")
            return result
        except (json.JSONDecodeError, TypeError):
            continue  # Try next match

    # Path 3: All parsing attempts failed - log for debugging
    preview = raw_text[:500] if len(raw_text) > 500 else raw_text
    print(f"[JSON_EXTRACT] PARSE_FAILED - logging full response for debugging:")
    print(f"--- RAW RESPONSE START ---")
    print(raw_text)
    print(f"--- RAW RESPONSE END (len={len(raw_text)}) ---")
    return None


def safe_parse_llm_response(raw_text: str) -> Dict[str, Any]:
    """
    Parse LLM response text into a dict, with robust fallback.

    Returns:
        Parsed dict on success.
        Default valid JSON dict on failure: {"text": "...", "error": "parse_failed"}

    Never raises; always returns a valid JSON-serializable dict.
    """
    result = extract_json_from_text(raw_text)

    if result is not None:
        return result

    # Fallback: return a valid dict with error info and truncated text
    fallback = {
        "text": raw_text[:200] if raw_text else "(empty response)",
        "error": "parse_failed",
        "raw_length": len(raw_text) if raw_text else 0,
    }
    print(f"[JSON_EXTRACT] fallback_used raw_length={fallback['raw_length']}")
    return fallback


# ── Exceptions ─────────────────────────────────────────────────────────────────

class LLMCircuitOpenError(RuntimeError):
    pass


# ── LLM Client ────────────────────────────────────────────────────────────────

class LLMClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or LLM_SPACE_URL or "http://localhost:7860"
        self.token = token or LLM_API_TOKEN
        self._headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=httpx.Timeout(timeout=LLM_DEFAULT_TIMEOUT, connect=LLM_CONNECT_TIMEOUT),
        )
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0
        self._metrics = get_orchestration_metrics()

    def _is_circuit_open(self) -> bool:
        return self._breaker_open_until > asyncio.get_running_loop().time()

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= LLM_BREAKER_FAIL_THRESHOLD:
            now = asyncio.get_running_loop().time()
            self._breaker_open_until = now + LLM_BREAKER_COOLDOWN_SECONDS

    def circuit_state(self) -> Dict[str, Any]:
        return {
            "open": self._is_circuit_open(),
            "consecutive_failures": self._consecutive_failures,
            "open_until": self._breaker_open_until,
        }

    async def _post_json(self, path: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        """
        POST to LLM endpoint and parse JSON response with robust extraction.

        - Uses safe_parse_llm_response() instead of response.json() directly.
        - This handles cases where LLM returns extra text around the JSON block.
        - Falls back gracefully instead of raising parse errors.
        """
        if self._is_circuit_open():
            self._metrics.increment(f"llm.{path}.circuit_open")
            print(f"[LLM] circuit_open path={path} timeout={timeout}s")
            raise LLMCircuitOpenError("LLM circuit is open")

        last_error: Optional[Exception] = None
        attempts = max(1, LLM_MAX_RETRIES + 1)
        payload_keys = sorted(payload.keys())
        print(
            f"[LLM] start path={path} base_url={self.base_url} timeout={timeout}s "
            f"attempts={attempts} payload_keys={payload_keys}"
        )
        for attempt in range(attempts):
            start = time.perf_counter()
            try:
                response = await asyncio.wait_for(self._client.post(path, json=payload), timeout=timeout)
                response.raise_for_status()
                self._record_success()
                self._metrics.increment(f"llm.{path}.success")
                duration = time.perf_counter() - start
                self._metrics.observe_latency(f"llm.{path}.latency", duration)

                # ── Use robust JSON parsing instead of response.json() ──────────────
                raw_text = response.text
                raw_preview = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
                print(
                    f"[LLM] success path={path} attempt={attempt + 1}/{attempts} "
                    f"status={response.status_code} duration_ms={duration * 1000:.1f} "
                    f"response_preview={raw_preview}"
                )
                return safe_parse_llm_response(raw_text)

            except (asyncio.TimeoutError, httpx.HTTPError, httpx.RequestError) as exc:
                last_error = exc
                self._record_failure()
                self._metrics.increment(f"llm.{path}.failure")
                duration = time.perf_counter() - start
                self._metrics.observe_latency(f"llm.{path}.latency", duration)
                print(
                    f"[LLM] failure path={path} attempt={attempt + 1}/{attempts} "
                    f"error={type(exc).__name__}: {exc} duration_ms={duration * 1000:.1f}"
                )
                if attempt >= attempts - 1:
                    raise
                delay = LLM_RETRY_BASE_DELAY * (2 ** attempt)
                self._metrics.record_event(f"llm.{path}.retry", {"attempt": attempt + 1, "delay": delay})
                print(f"[LLM] retry path={path} next_delay_s={delay:.2f}")
                await asyncio.sleep(delay)

        if last_error:
            raise last_error
        raise RuntimeError("Unexpected LLM post_json state")

    async def classify(
        self,
        text: str,
        timeout: float = LLM_CLASSIFY_TIMEOUT,
        max_tokens: int = LLM_CLASSIFY_MAX_TOKENS,
        temperature: float = LLM_FAST_TEMPERATURE,
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": min(0.3, LLM_TOP_P),
            "repeat_penalty": 1.03,
        }
        return await self._post_json("/classify", payload, timeout)

    async def split(
        self,
        text: str,
        timeout: float = LLM_SPLIT_TIMEOUT,
        max_tokens: int = LLM_SPLIT_MAX_TOKENS,
        temperature: float = LLM_FAST_TEMPERATURE,
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": min(0.3, LLM_TOP_P),
            "repeat_penalty": 1.03,
        }
        return await self._post_json("/split", payload, timeout)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = LLM_GENERATE_MAX_TOKENS,
        temperature: float = LLM_GENERATE_TEMPERATURE,
        timeout: float = LLM_GENERATE_TIMEOUT,
        top_p: float = LLM_TOP_P,
        repeat_penalty: float = LLM_REPEAT_PENALTY,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
        }
        if stop:
            payload["stop"] = stop
        return await self._post_json("/generate", payload, timeout)

    async def close(self):
        await self._client.aclose()
