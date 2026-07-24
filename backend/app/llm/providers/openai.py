"""
OpenAI LLM Provider using official async openai SDK.
"""
from __future__ import annotations

import json
from typing import Any
import openai
import structlog

from app.core.config import settings
from app.core.exceptions import LLMProviderError, LLMProviderNotConfiguredError
from app.llm.base import LLMProvider, LLMResponse

log = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise LLMProviderNotConfiguredError("OPENAI_API_KEY is not configured.")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model = model or "gpt-4o-mini"

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        formatted_msgs = []
        if system:
            formatted_msgs.append({"role": "system", "content": system})
        formatted_msgs.extend(messages)

        try:
            res = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_msgs,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
            )
            msg = res.choices[0].message
            usage = res.usage
            return LLMResponse(
                content=msg.content or "",
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
            )
        except Exception as e:
            log.error("llm.openai.error", error=str(e))
            raise LLMProviderError(f"OpenAI API call failed: {e}") from e

    async def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        sys_prompt = (system or "You are a memory extraction engine.") + "\nRespond strictly in valid JSON matching this schema:\n" + json.dumps(schema)
        res = await self.complete(
            messages=[{"role": "user", "content": text}],
            system=sys_prompt,
            temperature=0.0,
        )
        try:
            return json.loads(res.content)
        except json.JSONDecodeError:
            return {}
