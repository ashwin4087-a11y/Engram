"""
LLM Provider Factory — instantiates configured LLM provider.
"""
from __future__ import annotations

import structlog
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.providers.anthropic import AnthropicProvider
from app.llm.providers.gemini import GeminiProvider, OllamaProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai import OpenAIProvider

log = structlog.get_logger(__name__)


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
    log.info("llm.factory.get_provider", provider=name)

    if name == "anthropic":
        return AnthropicProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "gemini":
        return GeminiProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "mock":
        return MockLLMProvider()
    else:
        log.warning("llm.factory.unknown_provider", provider=name, fallback="mock")
        return MockLLMProvider()
