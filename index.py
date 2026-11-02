"""Vercel entrypoint.

Vercel looks for a ``FastAPI`` instance named ``app`` in ``index.py`` at the
project root. The application itself lives in ``backend/`` (that is also where
``uvicorn app.main:app`` runs from locally), so this file simply puts that
folder on the import path and re-exports the app.

Nothing else belongs here: keeping the shim tiny means the same code runs on
Vercel, in Docker and on a normal server.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import ensure_pool  # noqa: E402
from app.main import app  # noqa: E402,F401

# Serverless platforms may skip lifespan startup on a cold start, so the
# connection pool is opened here as soon as the module is imported. The call is
# idempotent: warm invocations reuse the same pool.
ensure_pool()
