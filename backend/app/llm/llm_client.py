import asyncio
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from app.agents.orchestration_metrics import get_orchestration_metrics


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

EXTERNAL_CONNECT_TIMEOUT = float(os.environ.get("EXTERNAL_CONNECT_TIMEOUT", "5"))
EXTERNAL_DEFAULT_TIMEOUT = float(os.environ.get("EXTERNAL_DEFAULT_TIMEOUT", "10"))

LLM_CONNECT_TIMEOUT = float(os.environ.get("LLM_CONNECT_TIMEOUT", "5"))
LLM_DEFAULT_TIMEOUT = float(os.environ.get("LLM_DEFAULT_TIMEOUT", "10"))

LLM_SPLIT_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", "3"))
LLM_CLASSIFY_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2"))
LLM_GENERATE_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "25"))

LLM_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "128"))
LLM_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "64"))
LLM_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "160"))

LLM_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.2"))
LLM_FAST_TEMPERATURE = float(os.environ.get("LLM_FAST_TEMPERATURE", "0.0"))
LLM_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
LLM_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "1"))
LLM_RETRY_BASE_DELAY = float(os.environ.get("LLM_RETRY_BASE_DELAY", "0.5"))
LLM_BREAKER_FAIL_THRESHOLD = int(os.environ.get("LLM_BREAKER_FAIL_THRESHOLD", "5"))
LLM_BREAKER_COOLDOWN_SECONDS = float(os.environ.get("LLM_BREAKER_COOLDOWN_SECONDS", "30"))

INTENT_LABELS = (
    "grade_view",
    "learned_subjects_view",
    "student_info",
    "subject_info",
    "class_info",
    "schedule_view",
    "schedule_info",
    "subject_registration_suggestion",
    "class_registration_suggestion",
    "modify_schedule",
    "graduation_progress",
    "unknown",
)

INTENT_CLASSIFY_SYSTEM_PROMPT = (
    "Ban la bo phan phan loai intent cho tro ly hoc vu bang tieng Viet. "
    "Chi tra ve JSON hop le voi cac khoa intent, confidence, reason. "
    f"Intent hop le: {', '.join(INTENT_LABELS)}. "
    "confidence la so thuc trong khoang 0 den 1. "
    "Neu cau hoi noi ve dang ky mon hoc, nen hoc mon nao, tu van mon hoc thi uu tien "
    "subject_registration_suggestion. Neu khong du can cu thi tra ve unknown."
)

QUERY_SPLIT_SYSTEM_PROMPT = (
    "Nhiem vu cua ban la tach cau hoi phuc thanh cac y dinh hanh dong doc lap. "
    "Cac cau rang buoc nhu 'khong muon hoc X' phai duoc gan vao cung segment voi hanh dong ma no bo nghia. "
    "Vi du: 'Dang ky mon nao va khong hoc mon X' la 1 segment. "
    "Chi tra ve JSON hop le voi khoa duy nhat la segments va gia tri la mang chuoi."
)


def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None

    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass

    json_pattern = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}", re.DOTALL)
    for match in json_pattern.finditer(raw_text):
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue

    print("[JSON_EXTRACT] PARSE_FAILED - logging full response:")
    print("--- RAW RESPONSE START ---")
    print(raw_text)
    print(f"--- RAW RESPONSE END (len={len(raw_text)}) ---")
    return None


def safe_parse_llm_response(raw_text: str) -> Dict[str, Any]:
    result = extract_json_from_text(raw_text)
    if result is not None:
        return result
    return {
        "text": raw_text[:200] if raw_text else "(empty response)",
        "error": "parse_failed",
        "raw_length": len(raw_text) if raw_text else 0,
    }


class LLMCircuitOpenError(RuntimeError):
    pass


class LLMAPIError(RuntimeError):
    pass


class LLMTimeoutError(RuntimeError):
    pass


class GeminiClient:
    """Retained for compatibility; not used by classify/split."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.0-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
        timeout: float = 25.0,
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9,
            },
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(self.url, json=payload, headers=headers, params=params, timeout=timeout),
                    timeout=timeout,
                )
            if response.status_code != 200:
                raise LLMAPIError(f"Gemini API error: {response.status_code}")
            data = response.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"text": text, "raw_response": data}
        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError("Gemini timeout") from exc


class OpenAIClient:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or OPENAI_MODEL
        self.url = "https://api.openai.com/v1/chat/completions"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 160,
        temperature: float = 0.2,
        timeout: float = 25.0,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=timeout, connect=min(timeout, EXTERNAL_CONNECT_TIMEOUT))
            ) as client:
                response = await asyncio.wait_for(
                    client.post(self.url, json=payload, headers=headers),
                    timeout=timeout,
                )
            if response.status_code != 200:
                raise LLMAPIError(f"OpenAI API error: {response.status_code} {response.text[:300]}")
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise LLMAPIError("No choices in OpenAI response")
            text = choices[0].get("message", {}).get("content", "")
            duration_ms = (time.perf_counter() - start) * 1000
            print(f"[OPENAI] model={self.model} duration_ms={duration_ms:.1f}")
            return {"text": text, "raw_response": data}
        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError("OpenAI timeout") from exc


class LLMClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = None
        self.token = None
        self._headers = {}
        self._openai = OpenAIClient(OPENAI_API_KEY, model=OPENAI_MODEL) if OPENAI_API_KEY else None
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0
        self._metrics = get_orchestration_metrics()
        if self._openai:
            print(f"[LLM] OpenAI client initialized (model={OPENAI_MODEL})")

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

    async def _require_openai(self) -> OpenAIClient:
        if not self._openai:
            raise LLMAPIError("OPENAI_API_KEY is not configured")
        return self._openai

    async def _complete_json(
        self,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        timeout: float,
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        if self._is_circuit_open():
            self._metrics.increment(f"llm.{operation}.circuit_open")
            raise LLMCircuitOpenError("LLM circuit is open")

        openai_client = await self._require_openai()
        attempts = max(1, LLM_MAX_RETRIES + 1)
        last_error: Optional[Exception] = None

        for attempt in range(attempts):
            started = time.perf_counter()
            try:
                result = await openai_client.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                )
                parsed = safe_parse_llm_response(result.get("text", ""))
                if parsed.get("error") == "parse_failed":
                    raise LLMAPIError(f"{operation} returned non-JSON payload")
                self._record_success()
                duration = time.perf_counter() - started
                self._metrics.increment(f"llm.{operation}.success")
                self._metrics.observe_latency(f"llm.{operation}.latency", duration)
                parsed["text"] = result.get("text", "")
                return parsed
            except Exception as exc:
                last_error = exc
                self._record_failure()
                duration = time.perf_counter() - started
                self._metrics.increment(f"llm.{operation}.failure")
                self._metrics.observe_latency(f"llm.{operation}.latency", duration)
                print(
                    f"[LLM] {operation} failed attempt={attempt + 1}/{attempts} "
                    f"error={type(exc).__name__}: {exc}"
                )
                if attempt >= attempts - 1:
                    raise
                await asyncio.sleep(LLM_RETRY_BASE_DELAY * (2 ** attempt))

        if last_error:
            raise last_error
        raise RuntimeError("Unexpected LLM completion state")

    async def classify(
        self,
        text: str,
        timeout: float = LLM_CLASSIFY_TIMEOUT,
        max_tokens: int = LLM_CLASSIFY_MAX_TOKENS,
        temperature: float = LLM_FAST_TEMPERATURE,
    ) -> Dict[str, Any]:
        result = await self._complete_json(
            operation="classify",
            system_prompt=INTENT_CLASSIFY_SYSTEM_PROMPT,
            user_prompt=f"Query: {text}",
            timeout=timeout,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result["intent"] = result.get("intent", "unknown")
        try:
            result["confidence"] = float(result.get("confidence", 0.0))
        except (TypeError, ValueError):
            result["confidence"] = 0.0
        return result

    async def split(
        self,
        text: str,
        timeout: float = LLM_SPLIT_TIMEOUT,
        max_tokens: int = LLM_SPLIT_MAX_TOKENS,
        temperature: float = LLM_FAST_TEMPERATURE,
    ) -> Dict[str, Any]:
        result = await self._complete_json(
            operation="split",
            system_prompt=QUERY_SPLIT_SYSTEM_PROMPT,
            user_prompt=f"Cau hoi: {text}",
            timeout=timeout,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        segments = result.get("segments")
        if not isinstance(segments, list):
            segments = [text]
        result["segments"] = [
            segment.strip() for segment in segments if isinstance(segment, str) and segment.strip()
        ] or [text]
        return result

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
        start = time.perf_counter()
        openai_timeout = float(os.environ.get("OPENAI_GENERATE_TIMEOUT", "25"))

        if self._openai:
            try:
                result = await self._openai.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=openai_timeout,
                )
                duration = (time.perf_counter() - start) * 1000
                self._record_success()
                self._metrics.increment("llm.generate.openai_success")
                self._metrics.observe_latency("llm.generate.latency", duration)
                return result
            except LLMTimeoutError:
                self._record_failure()
                self._metrics.increment("llm.generate.openai_timeout")
            except Exception as exc:
                self._record_failure()
                self._metrics.increment("llm.generate.openai_failure")
                print(f"[LLM:GENERATE] OpenAI failed: {type(exc).__name__}: {exc}")

        duration = (time.perf_counter() - start) * 1000
        self._metrics.increment("llm.generate.rulebase_fallback")
        self._metrics.observe_latency("llm.generate.latency", duration)
        return {
            "text": "Minh dang xu ly hoi cham, ban vui long thu lai trong giay lat nhe!",
            "model_used": "rulebase_fallback",
        }

    async def close(self):
        return None
