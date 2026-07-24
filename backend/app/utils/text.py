"""Text processing & precise token estimation utilities using tiktoken."""
from __future__ import annotations

import re
import unicodedata
import structlog

log = structlog.get_logger(__name__)

_tiktoken_encoding = None


def _get_tiktoken_encoding():
    global _tiktoken_encoding
    if _tiktoken_encoding is None:
        try:
            import tiktoken
            _tiktoken_encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tiktoken_encoding = False
    return _tiktoken_encoding if _tiktoken_encoding is not False else None


def normalize_text(text: str) -> str:
    """Normalize user input: strip, collapse whitespace, normalize unicode."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_entity_name(name: str) -> str:
    """Normalize an entity name for comparison/deduplication."""
    return normalize_text(name).lower()


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def estimate_tokens(text: str) -> int:
    """
    Calculate precise token count using tiktoken (cl100k_base).
    Falls back to character heuristic (~4 chars/token) if tiktoken is unavailable.
    """
    if not text:
        return 0
    enc = _get_tiktoken_encoding()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)
