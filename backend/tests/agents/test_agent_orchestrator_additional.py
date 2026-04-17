import sys
import asyncio
import time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.agent_orchestrator import AgentOrchestrator
from app.llm.response_cache import ResponseCache, InMemoryCache

class FakeLLMTimeout:
    async def split(self, text: str, **kwargs): raise asyncio.TimeoutError()
    async def classify(self, text: str, **kwargs): raise asyncio.TimeoutError()
    async def generate(self, prompt, max_tokens=256, temperature=0.2, **kwargs): return {"text": "fallback"}

class FakeToolsFail:
    def __init__(self): self.calls = 0
    async def call(self, name, payload):
        self.calls += 1
        raise Exception('tool failure')

class FakeTFIDFStatic:
    def __init__(self, label, score):
        self.label = label
        self.score = score
    def classify_intent(self, text: str): return (self.label, self.score)

@pytest.mark.asyncio
async def test_node1_fallback_on_llm_timeout():
    llm = FakeLLMTimeout()
    orch = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    text = "Cái gì đó. Và thêm câu hỏi?"
    segments = await orch.node1_query_splitter(text)
    assert isinstance(segments, list)
    assert len(segments) >= 2

@pytest.mark.asyncio
async def test_handle_tool_failure_is_recorded():
    llm = FakeLLMTimeout()
    tools = FakeToolsFail()
    orch = AgentOrchestrator(llm_client=llm, tools=None, cache=ResponseCache())
    orch.tfidf = FakeTFIDFStatic('some_tool', 0.9)
    orch.tools = tools
    res = await orch.handle('Test input')
    assert 'raw' in res
    assert any('error' in str(item.get('raw_result')) for item in res['raw'])

@pytest.mark.asyncio
async def test_node4_cache_expiry_triggers_second_generate():
    class CountingLLM:
        def __init__(self): self.generate_called = 0
        async def split(self, text, **kwargs): return {"segments": [text]}
        async def classify(self, text, **kwargs): return {"intent": "x", "confidence": 0.5}
        async def generate(self, prompt, max_tokens=256, temperature=0.2, **kwargs):
            self.generate_called += 1
            return {"text": f"gen-{self.generate_called}"}

    llm = CountingLLM()
    cache = ResponseCache(); cache.client = InMemoryCache()
    orch = AgentOrchestrator(llm_client=llm, tools=None, cache=cache)
    raw = {'k': 'v'}
    out1 = await orch.node4_response_formatter(raw, instruction='ins')
    h = orch._hash_raw_result(raw, 'ins')
    cache.client.store[h] = (cache.client.store[h][0], time.time() - 1)
    out2 = await orch.node4_response_formatter(raw, instruction='ins')
    assert out1 != out2
    assert llm.generate_called == 2
