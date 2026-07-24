"""Test suite for compiler pipeline."""
import pytest
from app.memory.compiler.types import PipelineInput
from app.memory.compiler.pipeline import MemoryCompilerPipeline
from app.llm.base import LLMProvider, LLMResponse

class DummyLLM(LLMProvider):
    async def extract_structured(self, text, schema, system=None):
        return {"preferences": [], "tasks": []}
        
    async def complete(self, messages, system=None, tools=None, temperature=0.7, max_tokens=1024):
        return LLMResponse(content="response")

@pytest.mark.asyncio
async def test_compiler_pipeline_initialization():
    llm = DummyLLM()
    pipeline = MemoryCompilerPipeline(llm_provider=llm)
    assert len(pipeline.stages) == 10
