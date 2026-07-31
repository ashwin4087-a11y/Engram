"""Static file serving for the frontend assets."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

router = APIRouter(tags=["Frontend"])


@router.get("/js/{path:path}", include_in_schema=False)
async def serve_js(path: str) -> FileResponse:
    asset_path = FRONTEND_DIR / "js" / path
    return FileResponse(asset_path, media_type="application/javascript")


@router.get("/css/{filename}", include_in_schema=False)
async def serve_css(filename: str) -> FileResponse:
    asset_path = FRONTEND_DIR / "css" / filename
    return FileResponse(asset_path, media_type="text/css")


@router.get("/assets/{path:path}", include_in_schema=False)
async def serve_assets(path: str) -> FileResponse:
    asset_path = FRONTEND_DIR / "assets" / path
    return FileResponse(asset_path)
