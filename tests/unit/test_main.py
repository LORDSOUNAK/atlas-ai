from __future__ import annotations

from fastapi.testclient import TestClient

from aetheros.main import create_app


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agents_endpoint_accepts_create_request() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/agents",
        json={
            "name": "planner",
            "model": "gpt-4o",
            "memory_scopes": ["SESSION"],
            "timeout_seconds": 30,
            "max_iterations": 5,
            "context_window_tokens": 4000,
        },
        params={"tenant_id": "tenant-1"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "planner"
