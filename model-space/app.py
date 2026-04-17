import json
import asyncio
import os
import re
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from llama_cpp import Llama
except Exception as exc:  # pragma: no cover - import guard for deployment image only
    raise RuntimeError("llama-cpp-python is required to run model-space") from exc


MODEL_PATH = os.getenv("MODEL_PATH", os.getenv("GGUF_MODEL_PATH", "/data/model.gguf"))
N_CTX = int(os.getenv("LLAMA_N_CTX", "2048"))
N_BATCH = int(os.getenv("LLAMA_N_BATCH", "512"))
N_THREADS = int(os.getenv("LLAMA_N_THREADS", str(max((os.cpu_count() or 4) // 2, 2))))
N_THREADS_BATCH = int(os.getenv("LLAMA_N_THREADS_BATCH", str(N_THREADS)))
N_GPU_LAYERS = int(os.getenv("LLAMA_N_GPU_LAYERS", "0"))
TOP_P = float(os.getenv("LLAMA_TOP_P", "0.9"))
REPEAT_PENALTY = float(os.getenv("LLAMA_REPEAT_PENALTY", "1.08"))
DEFAULT_GENERATE_TEMPERATURE = float(os.getenv("LLAMA_GENERATE_TEMPERATURE", "0.2"))
DEFAULT_FAST_TEMPERATURE = float(os.getenv("LLAMA_FAST_TEMPERATURE", "0.0"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "2"))
WARMUP_ON_STARTUP = os.getenv("WARMUP_ON_STARTUP", "true").strip().lower() == "true"
INFERENCE_TIMEOUT_SPLIT = float(os.getenv("INFERENCE_TIMEOUT_SPLIT", "8"))
INFERENCE_TIMEOUT_CLASSIFY = float(os.getenv("INFERENCE_TIMEOUT_CLASSIFY", "8"))
INFERENCE_TIMEOUT_GENERATE = float(os.getenv("INFERENCE_TIMEOUT_GENERATE", "20"))

ALLOWED_INTENTS = [
    "grade_view",
    "learned_subjects_view",
    "subject_info",
    "class_info",
    "schedule_view",
    "subject_registration_suggestion",
    "class_registration_suggestion",
    "modify_schedule",
    "student_info",
    "unknown",
]

_llm: Optional[Llama] = None
_llm_lock = Lock()
_loaded_at: Optional[str] = None
_request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

app = FastAPI(title="Qwen2 Agent Space", version="1.0.0")


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_tokens: int = Field(default=12, ge=1, le=64)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    top_p: float = Field(default=0.2, ge=0.0, le=1.0)
    repeat_penalty: float = Field(default=1.03, ge=1.0, le=2.0)


class SplitRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_tokens: int = Field(default=48, ge=1, le=128)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    top_p: float = Field(default=0.2, ge=0.0, le=1.0)
    repeat_penalty: float = Field(default=1.03, ge=1.0, le=2.0)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=160, ge=1, le=512)
    temperature: float = Field(default=DEFAULT_GENERATE_TEMPERATURE, ge=0.0, le=1.5)
    top_p: float = Field(default=TOP_P, ge=0.0, le=1.0)
    repeat_penalty: float = Field(default=REPEAT_PENALTY, ge=1.0, le=2.0)
    stop: Optional[List[str]] = None


def _load_llm() -> Llama:
    global _llm, _loaded_at
    if _llm is not None:
        return _llm

    with _llm_lock:
        if _llm is not None:
            return _llm

        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_threads=N_THREADS,
            n_threads_batch=N_THREADS_BATCH,
            n_gpu_layers=N_GPU_LAYERS,
            chat_format="chatml",
            verbose=False,
            use_mmap=True,
            use_mlock=False,
        )
        _loaded_at = "loaded"
        return _llm


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def _safe_json_loads(text: str) -> Dict[str, Any]:
    candidate = _strip_code_fences(text)
    try:
        return json.loads(candidate)
    except Exception:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _chat_completion_sync(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    repeat_penalty: float,
    stop: Optional[List[str]] = None,
) -> str:
    llm = _load_llm()
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
        stop=stop,
    )
    content = response["choices"][0]["message"]["content"]
    return content.strip()


async def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    repeat_penalty: float,
    timeout_seconds: float,
    stop: Optional[List[str]] = None,
) -> str:
    async with _request_semaphore:
        return await asyncio.wait_for(
            asyncio.to_thread(
                _chat_completion_sync,
                system_prompt,
                user_prompt,
                max_tokens,
                temperature,
                top_p,
                repeat_penalty,
                stop,
            ),
            timeout=timeout_seconds,
        )


@app.on_event("startup")
async def _warmup() -> None:
    _load_llm()
    if WARMUP_ON_STARTUP:
        try:
            await _chat_completion(
                system_prompt="Bạn là trợ lý kiểm tra sức khỏe model.",
                user_prompt="trả lời: ok",
                max_tokens=2,
                temperature=0.0,
                top_p=0.1,
                repeat_penalty=1.0,
                timeout_seconds=min(INFERENCE_TIMEOUT_CLASSIFY, 5.0),
                stop=["\n"],
            )
        except Exception:
            # Warmup failure should not crash startup; readiness/health will expose degraded status.
            pass


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "n_ctx": N_CTX,
        "n_batch": N_BATCH,
        "n_threads": N_THREADS,
        "loaded": _llm is not None,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy" if _llm is not None else "degraded",
        "loaded": _llm is not None,
        "warmup_on_startup": WARMUP_ON_STARTUP,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
    }


@app.post("/classify")
async def classify(request: ClassifyRequest) -> Dict[str, Any]:
    system_prompt = (
        "Bạn là bộ phân loại intent cho chatbot trường đại học. "
        "Chỉ trả về JSON hợp lệ, không markdown, không giải thích. "
        f"Intent hợp lệ: {', '.join(ALLOWED_INTENTS)}."
    )
    user_prompt = (
        "Phân loại đoạn văn sau vào đúng 1 intent. "
        "Trả về JSON đúng định dạng: {\"intent\": \"...\", \"confidence\": 0.0}.\n\n"
        f"Đoạn văn: {request.text}"
    )

    try:
        content = await _chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            repeat_penalty=request.repeat_penalty,
            timeout_seconds=INFERENCE_TIMEOUT_CLASSIFY,
            stop=["\n"]
        )
        parsed = _safe_json_loads(content)
        intent = str(parsed.get("intent") or "unknown")
        if intent not in ALLOWED_INTENTS:
            intent = "unknown"
        confidence = parsed.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0
        return {"intent": intent, "confidence": confidence, "text": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"classification failed: {exc}") from exc


@app.post("/split")
async def split(request: SplitRequest) -> Dict[str, Any]:
    system_prompt = (
        "Bạn tách câu hỏi phức hợp thành danh sách các câu hỏi đơn. "
        "Chỉ trả về JSON hợp lệ, không markdown, không giải thích."
    )
    user_prompt = (
        "Tách văn bản sau thành mảng JSON tên là segments. "
        "Nếu chỉ có 1 ý, trả về đúng 1 phần tử.\n\n"
        f"Văn bản: {request.text}\n\n"
        "Định dạng: {\"segments\": [\"...\"]}"
    )

    try:
        content = await _chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            repeat_penalty=request.repeat_penalty,
            timeout_seconds=INFERENCE_TIMEOUT_SPLIT,
            stop=["\n"]
        )
        parsed = _safe_json_loads(content)
        segments = parsed.get("segments") or []
        if isinstance(segments, str):
            segments = [segments]
        segments = [str(segment).strip() for segment in segments if str(segment).strip()]
        if not segments:
            segments = [request.text.strip()]
        return {"segments": segments, "text": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"split failed: {exc}") from exc


@app.post("/generate")
async def generate(request: GenerateRequest) -> Dict[str, Any]:
    system_prompt = (
        "Bạn là trợ lý trả lời tiếng Việt. "
        "Ưu tiên chính xác, ngắn gọn, không lặp, không bịa dữ liệu, không nhắc tới prompt nội bộ."
    )
    try:
        content = await _chat_completion(
            system_prompt=system_prompt,
            user_prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            repeat_penalty=request.repeat_penalty,
            timeout_seconds=INFERENCE_TIMEOUT_GENERATE,
            stop=request.stop,
        )
        return {"text": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"generation failed: {exc}") from exc