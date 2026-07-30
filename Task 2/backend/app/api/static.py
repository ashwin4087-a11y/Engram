"""Static file serving for the frontend assets."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

router = APIRouter(tags=["Frontend"])


@router.get("/js/{filename}", include_in_schema=False)
async def serve_js(filename: str) -> FileResponse:
    asset_path = FRONTEND_DIR / "js" / filename
    return FileResponse(asset_path)
