"""
Embedding generator module — generates 384-dimensional dense vector embeddings using Sentence Transformers (all-MiniLM-L6-v2).
Includes a thread-pool executor for non-blocking async execution and a deterministic math fallback if torch/sentence-transformers is offline.
"""
from __future__ import annotations

import asyncio
import math
from typing import Any
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)

_model: Any = None
_model_failed = False


def _get_sentence_transformer() -> Any:
    global _model, _model_failed
    if _model_failed:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            log.info("embeddings.loading_model", model=settings.EMBEDDING_MODEL)
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            log.info("embeddings.model_loaded", dim=settings.EMBEDDING_DIMENSION)
        except Exception as e:
            log.warning("embeddings.load_failed_using_fallback", error=str(e))
            _model_failed = True
            return None
    return _model


def _compute_fallback_embedding(text: str, dim: int = 384) -> list[float]:
    """Deterministic, normalized pseudo-embedding fallback for test/offline environments."""
    vector = [0.0] * dim
    for i, char in enumerate(text):
        idx = (ord(char) * (i + 1)) % dim
        vector[idx] += math.sin(ord(char) + i)

    # Normalize vector to unit length
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [round(x / norm, 6) for x in vector]


def _embed_text_sync(text: str) -> list[float]:
    model = _get_sentence_transformer()
    if model is not None:
        try:
            vec = model.encode(text, convert_to_numpy=True)
            return [float(x) for x in vec]
        except Exception as e:
            log.warning("embeddings.encode_failed", error=str(e))
    return _compute_fallback_embedding(text, settings.EMBEDDING_DIMENSION)


async def generate_embedding(text: str) -> list[float]:
    """Asynchronously generate a vector embedding for a single text string."""
    if not text.strip():
        return [0.0] * settings.EMBEDDING_DIMENSION
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _embed_text_sync, text)


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Asynchronously generate vector embeddings for a batch of text strings."""
    tasks = [generate_embedding(t) for t in texts]
    return await asyncio.gather(*tasks)
