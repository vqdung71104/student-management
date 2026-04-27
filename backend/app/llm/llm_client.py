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

# OpenAI Configuration for Node 4 formatting
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # gpt-4o, gpt-4o-mini, gpt-3.5-turbo

# External API Timeouts (much shorter for fast APIs)
EXTERNAL_CONNECT_TIMEOUT = float(os.environ.get("EXTERNAL_CONNECT_TIMEOUT", "5"))
EXTERNAL_DEFAULT_TIMEOUT = float(os.environ.get("EXTERNAL_DEFAULT_TIMEOUT", "10"))  # 10s hard cap for external APIs

# Internal LLM Timeouts (kept for fallback)
LLM_CONNECT_TIMEOUT = float(os.environ.get("LLM_CONNECT_TIMEOUT", "5"))
LLM_DEFAULT_TIMEOUT = float(os.environ.get("LLM_DEFAULT_TIMEOUT", "10"))  # 10s max

LLM_SPLIT_TIMEOUT = float(os.environ.get("LLM_SPLIT_TIMEOUT", os.environ.get("LLM_CLASSIFY_TIMEOUT", "2")))
LLM_CLASSIFY_TIMEOUT = float(os.environ.get("LLM_CLASSIFY_TIMEOUT", "2"))
LLM_GENERATE_TIMEOUT = float(os.environ.get("LLM_GENERATE_TIMEOUT", "10"))  # 10s max per call

LLM_SPLIT_MAX_TOKENS = int(os.environ.get("LLM_SPLIT_MAX_TOKENS", "48"))
LLM_CLASSIFY_MAX_TOKENS = int(os.environ.get("LLM_CLASSIFY_MAX_TOKENS", "12"))
LLM_GENERATE_MAX_TOKENS = int(os.environ.get("LLM_GENERATE_MAX_TOKENS", "160"))

LLM_GENERATE_TEMPERATURE = float(os.environ.get("LLM_GENERATE_TEMPERATURE", "0.2"))
LLM_FAST_TEMPERATURE = float(os.environ.get("LLM_FAST_TEMPERATURE", "0.0"))
LLM_TOP_P = float(os.environ.get("LLM_TOP_P", "0.9"))
LLM_REPEAT_PENALTY = float(os.environ.get("LLM_REPEAT_PENALTY", "1.08"))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "1"))  # max 1 retry so total wait ≤ 2 × timeout
LLM_RETRY_BASE_DELAY = float(os.environ.get("LLM_RETRY_BASE_DELAY", "0.5"))
LLM_BREAKER_FAIL_THRESHOLD = int(os.environ.get("LLM_BREAKER_FAIL_THRESHOLD", "5"))
LLM_BREAKER_COOLDOWN_SECONDS = float(os.environ.get("LLM_BREAKER_COOLDOWN_SECONDS", "30"))


# ── JSON Extraction Helper ─────────────────────────────────────────────────────

def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None

    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass

    json_pattern = re.compile(r'\{(?:[^{}]|\{[^{}]*\})*\}', re.DOTALL)

    for match in json_pattern.finditer(raw_text):
        candidate = match.group(0)
        try:
            result = json.loads(candidate)
            return result
        except (json.JSONDecodeError, TypeError):
            continue

    preview = raw_text[:500] if len(raw_text) > 500 else raw_text
    print(f"[JSON_EXTRACT] PARSE_FAILED - logging full response:")
    print(f"--- RAW RESPONSE START ---")
    print(raw_text)
    print(f"--- RAW RESPONSE END (len={len(raw_text)}) ---")
    return None


def safe_parse_llm_response(raw_text: str) -> Dict[str, Any]:
    result = extract_json_from_text(raw_text)

    if result is not None:
        return result

    fallback = {
        "text": raw_text[:200] if raw_text else "(empty response)",
        "error": "parse_failed",
        "raw_length": len(raw_text) if raw_text else 0,
    }
    return fallback


# ── Exceptions ─────────────────────────────────────────────────────────────────

class LLMCircuitOpenError(RuntimeError):
    pass

class LLMAPIError(RuntimeError):
    pass

class LLMTimeoutError(RuntimeError):
    pass


# ── External LLM Clients ────────────────────────────────────────────────────────

class GeminiClient:
    """Fast Gemini Flash client for Node 4 formatting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.0-flash"  # Fastest Gemini model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        
        # Log input
        input_preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        print(f"[GEMINI] INPUT:\n{input_preview}")
        
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9,
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(self.url, json=payload, headers=headers, params=params, timeout=timeout),
                    timeout=timeout
                )
            
            duration = (time.perf_counter() - start) * 1000
            print(f"[GEMINI] RESPONSE_TIME: {duration:.1f}ms")
            
            if response.status_code != 200:
                print(f"[GEMINI] ERROR: status={response.status_code} body={response.text[:500]}")
                raise LLMAPIError(f"Gemini API error: {response.status_code}")
            
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                # Check for prompt feedback
                prompt_feedback = data.get("promptFeedback", {})
                block_reason = prompt_feedback.get("blockReason", "")
                if block_reason:
                    print(f"[GEMINI] BLOCKED: reason={block_reason}")
                    raise LLMAPIError(f"Prompt blocked: {block_reason}")
                raise LLMAPIError("No candidates in response")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise LLMAPIError("No parts in response")
            
            text = parts[0].get("text", "")
            
            # Log output
            output_preview = text[:300] + "..." if len(text) > 300 else text
            print(f"[GEMINI] OUTPUT:\n{output_preview}")
            
            return {"text": text, "raw_response": data}
            
        except asyncio.TimeoutError:
            duration = (time.perf_counter() - start) * 1000
            print(f"[GEMINI] TIMEOUT: {duration:.1f}ms exceeded {timeout}s")
            raise LLMTimeoutError(f"Gemini timeout after {duration:.1f}ms")
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            print(f"[GEMINI] ERROR: {type(e).__name__}: {str(e)} after {duration:.1f}ms")
            raise


class OpenAIClient:
    """Fast OpenAI GPT client for Node 4 formatting"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or OPENAI_MODEL  # configurable via OPENAI_MODEL env var
        self.url = "https://api.openai.com/v1/chat/completions"
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        
        # Log input
        input_preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        print(f"[OPENAI] INPUT:\n{input_preview}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(self.url, json=payload, headers=headers, timeout=timeout),
                    timeout=timeout
                )
            
            duration = (time.perf_counter() - start) * 1000
            print(f"[OPENAI] RESPONSE_TIME: {duration:.1f}ms")
            
            if response.status_code != 200:
                print(f"[OPENAI] ERROR: status={response.status_code} body={response.text[:500]}")
                raise LLMAPIError(f"OpenAI API error: {response.status_code}")
            
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise LLMAPIError("No choices in response")
            
            text = choices[0].get("message", {}).get("content", "")
            
            # Log output
            output_preview = text[:300] + "..." if len(text) > 300 else text
            print(f"[OPENAI] OUTPUT:\n{output_preview}")
            
            return {"text": text, "raw_response": data}
            
        except asyncio.TimeoutError:
            duration = (time.perf_counter() - start) * 1000
            print(f"[OPENAI] TIMEOUT: {duration:.1f}ms exceeded {timeout}s")
            raise LLMTimeoutError(f"OpenAI timeout after {duration:.1f}ms")
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            print(f"[OPENAI] ERROR: {type(e).__name__}: {str(e)} after {duration:.1f}ms")
            raise


# ── LLM Client ────────────────────────────────────────────────────────────────

class LLMClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or LLM_SPACE_URL or "http://localhost:7860"
        self.token = token or LLM_API_TOKEN
        self._headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        # OpenAI external client (default for Node 4 formatting)
        self._openai = OpenAIClient(OPENAI_API_KEY, model=OPENAI_MODEL) if OPENAI_API_KEY else None
        if self._openai:
            print(f"[LLM] OpenAI client initialized (model={OPENAI_MODEL})")

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
        """
        Generate response using OpenAI API for Node 4 formatting.
        Falls back to internal HF space if OpenAI fails.
        """
        start = time.perf_counter()

        # Log the INPUT to LLM
        input_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        print(f"\n{'='*60}")
        print(f"[LLM:GENERATE] INPUT:")
        print(f"{input_preview}")
        print(f"{'='*60}\n")

        # Try OpenAI external API first
        if self._openai:
            try:
                result = await self._openai.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=min(timeout, 15.0),
                )
                duration = (time.perf_counter() - start) * 1000
                self._record_success()
                self._metrics.increment("llm.generate.openai_success")
                self._metrics.observe_latency("llm.generate.latency", duration)

                output_text = result.get("text", "")
                output_preview = output_text[:300] + "..." if len(output_text) > 300 else output_text
                print(f"\n{'='*60}")
                print(f"[LLM:GENERATE] OUTPUT (OpenAI, {duration:.1f}ms):")
                print(f"{output_preview}")
                print(f"{'='*60}\n")

                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                print(f"[LLM:GENERATE] OpenAI failed: {type(e).__name__}: {str(e)} after {duration:.1f}ms")
                self._record_failure()
                self._metrics.increment("llm.generate.openai_failure")
                # Fall through to internal fallback

        # Fallback to internal HF space
        print(f"[LLM:GENERATE] Falling back to internal LLM space: {self.base_url}")
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repeat_penalty": repeat_penalty,
            }
            if stop:
                payload["stop"] = stop
            
            result = await self._post_json("/generate", payload, timeout)
            duration = (time.perf_counter() - start) * 1000
            self._metrics.increment("llm.generate.internal_success")
            self._metrics.observe_latency("llm.generate.latency", duration)
            
            output_text = result.get("text", str(result))
            output_preview = output_text[:300] + "..." if len(output_text) > 300 else output_text
            print(f"\n{'='*60}")
            print(f"[LLM:GENERATE] OUTPUT (Internal, {duration:.1f}ms):")
            print(f"{output_preview}")
            print(f"{'='*60}\n")
            
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            print(f"[LLM:GENERATE] Internal LLM FAILED: {type(e).__name__}: {str(e)} after {duration:.1f}ms")
            self._record_failure()
            self._metrics.increment("llm.generate.failure")
            
            # Return a fallback response instead of raising
            print(f"[LLM:GENERATE] Returning fallback response")
            fallback_text = f"Không thể xử lý yêu cầu. Vui lòng thử lại sau."
            return {"text": fallback_text, "error": str(e)}

    async def close(self):
        await self._client.aclose()
