import sys
import asyncio
from pathlib import Path
import pytest

# Add backend dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.agent_orchestrator import AgentOrchestrator
from app.llm.response_cache import ResponseCache

class FakeLLM:
    def __init__(self):
        self.split_called = 0
        self.classify_called = 0
        self.generate_called = 0

    async def split(self, text: str, **kwargs):
        self.split_called += 1
        return {"segments": [text], "raw": "ok"}

    async def classify(self, text: str, **kwargs):
        self.classify_called += 1
        return {"intent": "grade_view", "confidence": 0.85}

    async def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, **kwargs):
        self.generate_called += 1
        return {"text": f"Generated: {prompt[:30]}"}

class FakeTFIDF:
    def __init__(self, label: str, score: float):
        self._label = label
        self._score = score

    async def classify_intent(self, text: str):
        return {"intent": self._label, "confidence_score": self._score}

@pytest.mark.asyncio
async def test_node1_short_text_no_llm_call():
    llm = FakeLLM()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    orchestrator.tfidf = None
    text = "Xin chào"
    segments = await orchestrator.node1_query_splitter(text)
    assert segments == [text]
    assert llm.split_called == 0

@pytest.mark.asyncio
async def test_node2_uses_tfidf_when_high_confidence():
    llm = FakeLLM()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    orchestrator.tfidf = FakeTFIDF('grade_view', 0.9)
    res = await orchestrator.node2_intent_router("Cho tôi điểm")
    assert res['source'] == 'tfidf'
    assert res['intent'] == 'grade_view'
    assert llm.classify_called == 0

@pytest.mark.asyncio
async def test_node2_fallback_to_llm_when_low_confidence_and_long_text():
    llm = FakeLLM()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    orchestrator.tfidf = FakeTFIDF('unknown', 0.1)
    long_text = ' '.join(['từ'] * 25)
    res = await orchestrator.node2_intent_router(long_text)
    assert res['source'] == 'llm'
    assert llm.classify_called == 1

@pytest.mark.asyncio
async def test_node4_caching_behavior():
    llm = FakeLLM()
    cache = ResponseCache()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=cache)
    raw_result = {'a': 1}
    out1 = await orchestrator.node4_response_formatter(raw_result, instruction="Format")
    out2 = await orchestrator.node4_response_formatter(raw_result, instruction="Format")
    # `node4_response_formatter` returns a dict with 'text' and 'from_cache' keys
    assert isinstance(out1, dict), "Node4 must return a dict"
    assert isinstance(out2, dict), "Node4 must return a dict"
    assert 'text' in out1, "Dict must have 'text' key"
    assert 'text' in out2, "Dict must have 'text' key"
    assert out1['text'] == out2['text'], "Cached text must match"
    assert out1.get('from_cache') is False, "First call must not be cached"
    assert out2.get('from_cache') is True, "Second call must be cached"
    assert llm.generate_called == 1, "LLM generate must be called exactly once"


@pytest.mark.asyncio
async def test_handle_returns_normalized_contract_fields():
    llm = FakeLLM()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    orchestrator.tfidf = None
    result = await orchestrator.handle("cho toi xem diem")
    assert "raw" in result
    assert "response" in result
    assert "text" in result
    assert "intent" in result
    assert "confidence" in result
    assert "parts" in result
    assert result["text"] == result["response"]


@pytest.mark.asyncio
async def test_node4_formatter_fallback_text_on_generate_error():
    class BrokenGenerateLLM(FakeLLM):
        async def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2, **kwargs):
            raise RuntimeError("boom")

    llm = BrokenGenerateLLM()
    orchestrator = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    out = await orchestrator.node4_response_formatter({"x": 1}, instruction="Format")
    # `node4_response_formatter` returns a dict — check keys explicitly
    assert isinstance(out, dict), "Node4 must return a dict"
    assert 'text' in out, "Dict must have 'text' key"
    assert 'model_used' in out, "Dict must have 'model_used' key"
    assert len(out['text']) > 0, "Fallback text must not be empty"
    assert out['model_used'] == 'error', "model_used must be 'error' when generate raises"
