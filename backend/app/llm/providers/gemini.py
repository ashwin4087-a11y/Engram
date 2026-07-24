"""
Google Gemini & Ollama provider implementations.
"""
from __future__ import annotations

import json
from typing import Any
import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import LLMProviderError, LLMProviderNotConfiguredError
from app.llm.base import LLMProvider, LLMResponse

log = structlog.get_logger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise LLMProviderNotConfiguredError("GEMINI_API_KEY is not configured.")
        self.model = model or "gemini-1.5-flash"

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system}"}]})
        for m in messages:
            contents.append({"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return LLMResponse(content=text, prompt_tokens=0, completion_tokens=0)
            except Exception as e:
                log.error("llm.gemini.error", error=str(e))
                raise LLMProviderError(f"Gemini API call failed: {e}") from e

    async def extract_structured(
        self, text: str, schema: dict[str, Any], system: str | None = None
    ) -> dict[str, Any]:
        sys_prompt = (system or "Extract JSON matching schema:") + f"\nSchema: {json.dumps(schema)}"
        res = await self.complete([{"role": "user", "content": text}], system=sys_prompt, temperature=0.0)
        try:
            cleaned = res.content.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(cleaned)
        except Exception:
            return {}


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:latest") -> None:
        self.base_url = base_url
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        formatted_msgs = []
        if system:
            formatted_msgs.append({"role": "system", "content": system})
        formatted_msgs.extend(messages)

        payload = {"model": self.model, "messages": formatted_msgs, "stream": False, "options": {"temperature": temperature}}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return LLMResponse(content=data.get("message", {}).get("content", ""))
            except Exception as e:
                log.error("llm.ollama.error", error=str(e))
                raise LLMProviderError(f"Ollama API call failed: {e}") from e

    async def extract_structured(
        self, text: str, schema: dict[str, Any], system: str | None = None
    ) -> dict[str, Any]:
        sys_prompt = (system or "Extract JSON:") + f"\nSchema: {json.dumps(schema)}"
        res = await self.complete([{"role": "user", "content": text}], system=sys_prompt, temperature=0.0)
        try:
            return json.loads(res.content)
        except Exception:
            return {}
