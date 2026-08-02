from __future__ import annotations

from app.main import app


def test_app_entrypoint_exports_fastapi_app() -> None:
    assert app is not None
