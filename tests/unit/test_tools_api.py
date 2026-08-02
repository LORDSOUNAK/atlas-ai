from __future__ import annotations

from fastapi.testclient import TestClient

from aetheros.main import create_app


def test_tools_register_and_get() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {
        "tenant_id": "tenant-1",
        "name": "weather",
        "description": "desc",
        "tool_type": "EXTERNAL",
        "tool_schema": {"name": "weather"},
    }

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.post(
        "/api/v1/tools", params={"tenant_id": "tenant-1"}, json=payload, headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "weather"

    resp = client.get("/api/v1/tools", params={"tenant_id": "tenant-1"}, headers=headers)
    assert resp.status_code == 200
    arr = resp.json()
    assert len(arr) >= 1
