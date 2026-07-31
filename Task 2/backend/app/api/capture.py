"""Capture API
POST /capture - Accepts multipart/form-data `file` (image) and `metadata` (JSON string)
Saves image bytes and stores metadata via CaptureStorage service.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import json
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.dependencies import tracker_service
from app.services.capture_storage import CaptureStorage
from app.core.settings import settings

router = APIRouter(tags=['Capture'])

# simple singleton storage instance
capture_storage = CaptureStorage()


@router.post('/capture', summary='Upload captured frame')
async def upload_capture(file: UploadFile = File(...), metadata: Optional[str] = Form(None)):
    try:
        content = await file.read()
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except Exception:
                meta = {'raw': metadata}

        record = capture_storage.save(content, meta)

        return JSONResponse({'success': True, 'capture_id': record['id'], 'path': record['path'], 'metadata': record['metadata']})
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)}, status_code=500)


@router.get('/captures', summary='List stored captures')
async def list_captures(limit: int = 100):
    try:
        items = capture_storage.list(limit)
        return JSONResponse({'success': True, 'data': items})
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)}, status_code=500)


@router.get('/captures/{filename}', summary='Get capture image')
async def get_capture_image(filename: str):
    # Safely serve files from the captures directory
    try:
        base = Path(settings.DATA_DIR) / 'captures'
        file_path = base / filename
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Not found'}, status_code=404)
        return FileResponse(path=str(file_path.resolve()), media_type='image/jpeg')
    except Exception as e:
        return JSONResponse({'success': False, 'message': str(e)}, status_code=500)
