"""
Mock LLM Provider for offline/test environments and initial development.
Returns deterministic structured memory extraction without external API calls.
"""
from __future__ import annotations

import json
from typing import Any
from app.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        last_msg = messages[-1]["content"] if messages else ""
        reply = f"[Mock Agent Response] Processed input: '{last_msg[:60]}...'"
        return LLMResponse(content=reply, prompt_tokens=15, completion_tokens=20)

    async def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        # Deterministic extraction logic based on text keywords
        entities = []
        facts = []
        relationships = []
        
        lower_text = text.lower()
        if "berlin" in lower_text or "live" in lower_text or "move" in lower_text:
            entities.append({"name": "User", "type": "person", "importance": 0.9})
            entities.append({"name": "Berlin", "type": "location", "importance": 0.8})
            facts.append({"entity_name": "User", "statement": "User lives in Berlin", "importance": 0.85})
            relationships.append({
                "source": "User", "target": "Berlin", "relation_type": "located_in", "confidence": 0.95
            })

        if "python" in lower_text or "fastapi" in lower_text or "code" in lower_text:
            entities.append({"name": "Python", "type": "technology", "importance": 0.85})
            facts.append({"entity_name": "User", "statement": "User builds backend systems in Python", "importance": 0.8})
            relationships.append({
                "source": "User", "target": "Python", "relation_type": "uses", "confidence": 0.9
            })

        if not entities:
            entities.append({"name": "User", "type": "person", "importance": 0.7})
            facts.append({"entity_name": "User", "statement": f"User said: {text[:50]}", "importance": 0.5})

        return {
            "entities": entities,
            "facts": facts,
            "relationships": relationships,
            "episode_summary": f"User discussed: {text[:80]}",
            "preferences": ["dark_mode"] if "dark mode" in lower_text else [],
            "tasks": ["build_backend"] if "build" in lower_text else [],
        }
