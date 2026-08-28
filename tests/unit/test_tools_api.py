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
        "/api/v1/tools",
        params={"tenant_id": "tenant-1"},
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "weather"

    resp = client.get(
        "/api/v1/tools",
        params={"tenant_id": "tenant-1"},
        headers=headers,
    )
    assert resp.status_code == 200
    arr = resp.json()
    assert len(arr) >= 1


def test_tools_get_by_id() -> None:
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
    create_resp = client.post(
        "/api/v1/tools",
        params={"tenant_id": "tenant-1"},
        json=payload,
        headers=headers,
    )
    tool_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/tools/{tool_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "weather"


def test_tools_get_by_id_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.get("/api/v1/tools/missing-tool", headers=headers)
    assert resp.status_code == 404


def test_tools_get_by_name() -> None:
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
    client.post(
        "/api/v1/tools",
        params={"tenant_id": "tenant-1"},
        json=payload,
        headers=headers,
    )

    resp = client.get(
        "/api/v1/tools/name/weather",
        params={"tenant_id": "tenant-1"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "weather"


def test_tools_get_by_name_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.get(
        "/api/v1/tools/name/missing",
        params={"tenant_id": "tenant-1"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_tools_delete_removes_tool() -> None:
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
    create_resp = client.post(
        "/api/v1/tools",
        params={"tenant_id": "tenant-1"},
        json=payload,
        headers=headers,
    )
    tool_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/tools/{tool_id}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/tools/{tool_id}", headers=headers)
    assert get_resp.status_code == 404


def test_tools_delete_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.delete("/api/v1/tools/missing-tool", headers=headers)
    assert resp.status_code == 404
