"""Compatibility entrypoint for the top-level task package.

This project has both a root-level app package and a backend app package.
The regression tests import the root-level package, so the root entrypoint now
re-exports the production backend app to guarantee one consistent route surface.
"""

from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.main import app as backend_app

app = backend_app
create_app = backend_app
