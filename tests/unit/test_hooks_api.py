from __future__ import annotations

from fastapi.testclient import TestClient

from aetheros.main import create_app


def test_hook_create_and_list_via_api() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/hooks",
        params={"tenant_id": "tenant-1"},
        json={
            "tenant_id": "tenant-1",
            "name": "pre-run-check",
            "event_type": "PRE_AGENT_RUN",
            "priority": 10,
            "action": "CONTINUE",
            "config": {"check": "ok"},
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "pre-run-check"

    response = client.get("/api/v1/hooks", params={"tenant_id": "tenant-1"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_hook_execute_via_api() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/hooks",
        params={"tenant_id": "tenant-1"},
        json={
            "tenant_id": "tenant-1",
            "name": "abort-hook",
            "event_type": "PRE_AGENT_RUN",
            "priority": 1,
            "action": "ABORT",
            "config": {"reason": "stop"},
        },
    )

    response = client.post(
        "/api/v1/hooks/execute",
        params={"tenant_id": "tenant-1", "event_type": "PRE_AGENT_RUN"},
        json={"input": "test"},
    )

    assert response.status_code == 200
    assert response.json()["hook_aborted"] is True


def test_hook_get_returns_existing_hook() -> None:
    app = create_app()
    client = TestClient(app)

    create_resp = client.post(
        "/api/v1/hooks",
        params={"tenant_id": "tenant-1"},
        json={
            "tenant_id": "tenant-1",
            "name": "my-hook",
            "event_type": "PRE_AGENT_RUN",
            "priority": 10,
            "action": "CONTINUE",
            "config": {"check": "ok"},
        },
    )
    hook_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/hooks/{hook_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "my-hook"


def test_hook_get_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/hooks/missing-hook")
    assert response.status_code == 404


def test_hook_delete_removes_hook() -> None:
    app = create_app()
    client = TestClient(app)

    create_resp = client.post(
        "/api/v1/hooks",
        params={"tenant_id": "tenant-1"},
        json={
            "tenant_id": "tenant-1",
            "name": "to-delete",
            "event_type": "PRE_AGENT_RUN",
            "priority": 10,
            "action": "CONTINUE",
            "config": {},
        },
    )
    hook_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/hooks/{hook_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/hooks/{hook_id}")
    assert get_resp.status_code == 404


def test_hook_delete_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.delete("/api/v1/hooks/missing-hook")
    assert response.status_code == 404
