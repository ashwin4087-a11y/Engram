"""Frontend entrypoint helpers for the dashboard UI."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

router = APIRouter(tags=["Frontend"])


@router.get("/", include_in_schema=False)
async def serve_dashboard() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(index_path)


@router.get("/index.html", include_in_schema=False)
async def serve_dashboard_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
