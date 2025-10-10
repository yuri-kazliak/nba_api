"""Package-level ASGI entrypoint for uvicorn."""

from .presentation.app import create_app

app = create_app()
