"""
Abstract base class for all LLM providers.
Enables pluggable model switching (Anthropic, OpenAI, Gemini, Ollama, Mock).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    tool_calls: list[dict[str, Any]] = []
    raw_response: Any = None
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(ABC):
    """Unified interface for LLM operations."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a chat completion."""
        pass

    @abstractmethod
    async def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured JSON matching a target schema using tool call / JSON mode."""
        pass
