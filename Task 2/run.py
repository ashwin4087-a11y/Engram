"""
run.py — Application Launcher
=============================

Starts the production FastAPI backend and serves the bundled frontend assets
from the backend module directory.
"""

import os
from pathlib import Path

import uvicorn


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    backend_dir = project_root / "backend"
    os.chdir(backend_dir)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
