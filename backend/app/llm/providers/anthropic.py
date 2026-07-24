"""
Anthropic LLM Provider using official async anthropic SDK.
"""
from __future__ import annotations

import json
from typing import Any
import anthropic
import structlog

from app.core.config import settings
from app.core.exceptions import LLMProviderError, LLMProviderNotConfiguredError
from app.llm.base import LLMProvider, LLMResponse

log = structlog.get_logger(__name__)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise LLMProviderNotConfiguredError("ANTHROPIC_API_KEY is not configured.")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model = model or settings.DEFAULT_LLM_MODEL or "claude-3-haiku-20240307"

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        try:
            res = await self.client.messages.create(**kwargs)
            text_content = ""
            tool_calls = []
            for block in res.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({"name": block.name, "input": block.input, "id": block.id})

            return LLMResponse(
                content=text_content,
                tool_calls=tool_calls,
                raw_response=res,
                prompt_tokens=res.usage.input_tokens,
                completion_tokens=res.usage.output_tokens,
            )
        except Exception as e:
            log.error("llm.anthropic.error", error=str(e))
            raise LLMProviderError(f"Anthropic API call failed: {e}") from e

    async def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        tool_def = {
            "name": "extract_schema",
            "description": "Extract structured memory delta from user message",
            "input_schema": schema,
        }
        sys_prompt = system or "You are a high-precision AI memory extraction engine."
        res = await self.complete(
            messages=[{"role": "user", "content": text}],
            system=sys_prompt,
            tools=[tool_def],
            temperature=0.0,
        )
        for tc in res.tool_calls:
            if tc["name"] == "extract_schema":
                return tc["input"]
        return {}
