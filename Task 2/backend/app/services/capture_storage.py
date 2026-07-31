"""
capture_storage.py — simple persistent storage for captured frames
===============================================================

Saves incoming image bytes to disk under DATA_DIR/captures and
appends metadata entries to a JSON lines index file for retrieval.
"""
import json
from pathlib import Path
from typing import Dict, Optional
import uuid

from app.core.settings import settings


class CaptureStorageError(Exception):
    pass


class CaptureStorage:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or settings.DATA_DIR) / 'captures'
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / 'captures.jsonl'

    def save(self, image_bytes: bytes, metadata: Dict) -> Dict:
        """Save image and metadata. Returns record with id and path."""
        try:
            cid = str(uuid.uuid4())
            filename = f"capture-{cid}.jpg"
            img_path = self.base_dir / filename
            with open(img_path, 'wb') as f:
                f.write(image_bytes)

            record = {
                'id': cid,
                'filename': filename,
                'path': str(img_path.resolve()),
                'metadata': metadata,
            }
            # append to index
            with open(self.index_file, 'a', encoding='utf-8') as idx:
                idx.write(json.dumps(record) + '\n')

            return record
        except Exception as e:
            raise CaptureStorageError(f"Failed to save capture: {e}")

    def list(self, limit: int = 100):
        if not self.index_file.exists():
            return []
        records = []
        with open(self.index_file, 'r', encoding='utf-8') as idx:
            for line in idx:
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
        return records[-limit:][::-1]
