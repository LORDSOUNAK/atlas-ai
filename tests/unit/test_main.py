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


def test_agents_lifecycle_across_requests() -> None:
    app = create_app()
    client = TestClient(app)

    # 1. Create agent
    create_resp = client.post(
        "/api/v1/agents",
        json={
            "name": "researcher",
            "model": "claude-3-5-sonnet",
            "memory_scopes": ["SESSION"],
            "timeout_seconds": 60,
            "max_iterations": 10,
            "context_window_tokens": 8000,
        },
        params={"tenant_id": "tenant-persist-1"},
    )
    assert create_resp.status_code == 201
    agent_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "IDLE"

    # 2. Start agent in subsequent request
    start_resp = client.post(f"/api/v1/agents/{agent_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "RUNNING"
    assert "id" in start_resp.json()

    # 3. List agents to verify state persisted
    list_resp = client.get("/api/v1/agents", params={"tenant_id": "tenant-persist-1"})
    assert list_resp.status_code == 200
    agents = list_resp.json()
    matching = [a for a in agents if a["id"] == agent_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "RUNNING"
