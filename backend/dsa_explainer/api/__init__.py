"""The local HTTP API (FastAPI) that the web app talks to."""

from .app import create_app

__all__ = ["create_app"]
