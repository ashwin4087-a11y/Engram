"""Memory retrieval & context routes."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_context_compiler, get_retrieval_engine
from app.llm.factory import get_llm_provider
from app.memory.context.compiler import ContextCompiler
from app.memory.retrieval.engine import HybridRetrievalEngine
from app.schemas.context import ContextBundleResponse, ReasonRequest, ReasonResponse
from app.schemas.memory import MemoryResponse

router = APIRouter(tags=["Memory & Retrieval"])


@router.get("/memory", response_model=MemoryResponse)
async def retrieve_memory(
    session_id: UUID = Query(...),
    query: str = Query(...),
    retrieval_engine: HybridRetrievalEngine = Depends(get_retrieval_engine),
) -> MemoryResponse:
    """Run hybrid retrieval over facts and episodes."""
    return await retrieval_engine.retrieve(session_id, query)


@router.get("/context", response_model=ContextBundleResponse)
async def get_context_bundle(
    session_id: UUID = Query(...),
    query: str = Query(""),
    token_budget: int = Query(1500),
    compiler: ContextCompiler = Depends(get_context_compiler),
) -> ContextBundleResponse:
    """Compile token-budget-aware context bundle."""
    return await compiler.compile_context(session_id, query, token_budget=token_budget)


@router.post("/reason", response_model=ReasonResponse)
async def reason(
    req: ReasonRequest,
    compiler: ContextCompiler = Depends(get_context_compiler),
) -> ReasonResponse:
    """Agent reasoning turn using just-in-time compiled context bundle."""
    bundle = await compiler.compile_context(req.session_id, req.query, token_budget=req.token_budget)
    llm = get_llm_provider()

    system_prompt = f"You are an AI assistant with access to a structured World Model context bundle.\n\n{bundle.context_text}"
    res = await llm.complete(messages=[{"role": "user", "content": req.query}], system=system_prompt)

    return ReasonResponse(
        session_id=req.session_id,
        response=res.content,
        context_token_count=bundle.token_count,
        memories_used=len(bundle.memories),
    )

