import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from app.agents.orchestration_metrics import get_orchestration_metrics

LLM_SPACE_URL = os.environ.get("LLM_SPACE_URL")
LLM_API_TOKEN = os.environ.get("LLM_API_TOKEN")
LLM_CONNECT_TIMEOUT = float(os.environ.get("LLM_CONNECT_TIMEOUT", "5"))
LLM_SPLIT_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", os.environ.get("LLM_CLASSIFY_TIMEOUT", "2")))
LLM_CLASSIFY_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2"))
LLM_GENERATE_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "12"))

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


class LLMCircuitOpenError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or LLM_SPACE_URL or "http://localhost:7860"
        self.token = token or LLM_API_TOKEN
        self._headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=httpx.Timeout(timeout=30.0, connect=LLM_CONNECT_TIMEOUT),
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
        if self._is_circuit_open():
            self._metrics.increment(f"llm.{path}.circuit_open")
            raise LLMCircuitOpenError("LLM circuit is open")

        last_error: Optional[Exception] = None
        attempts = max(1, LLM_MAX_RETRIES + 1)
        for attempt in range(attempts):
            start = time.perf_counter()
            try:
                response = await asyncio.wait_for(self._client.post(path, json=payload), timeout=timeout)
                response.raise_for_status()
                self._record_success()
                self._metrics.increment(f"llm.{path}.success")
                self._metrics.observe_latency(f"llm.{path}.latency", time.perf_counter() - start)
                return response.json()
            except (asyncio.TimeoutError, httpx.HTTPError, httpx.RequestError) as exc:
                last_error = exc
                self._record_failure()
                self._metrics.increment(f"llm.{path}.failure")
                self._metrics.observe_latency(f"llm.{path}.latency", time.perf_counter() - start)
                if attempt >= attempts - 1:
                    raise
                delay = LLM_RETRY_BASE_DELAY * (2 ** attempt)
                self._metrics.record_event(f"llm.{path}.retry", {"attempt": attempt + 1, "delay": delay})
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
