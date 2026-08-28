from __future__ import annotations

from fastapi.testclient import TestClient

from aetheros.main import create_app


def test_memory_api_create_and_list() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.post(
        "/api/v1/memory",
        params={
            "tenant_id": "tenant-1",
            "scope": "SESSION",
            "key": "k1",
            "value": "v1",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"] == "k1"

    resp = client.get(
        "/api/v1/memory",
        params={"tenant_id": "tenant-1", "scope": "SESSION"},
        headers=headers,
    )
    assert resp.status_code == 200
    arr = resp.json()
    assert len(arr) >= 1


def test_memory_api_clear() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    client.post(
        "/api/v1/memory",
        params={
            "tenant_id": "tenant-1",
            "scope": "SESSION",
            "key": "x",
            "value": "1",
        },
        headers=headers,
    )

    resp = client.delete(
        "/api/v1/memory",
        params={"tenant_id": "tenant-1", "scope": "SESSION"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "removed" in resp.json()


def test_memory_api_get_entry() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    create_resp = client.post(
        "/api/v1/memory",
        params={
            "tenant_id": "tenant-1",
            "scope": "SESSION",
            "key": "k1",
            "value": "v1",
        },
        headers=headers,
    )
    entry_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/memory/{entry_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["key"] == "k1"
    assert resp.json()["value"] == "v1"


def test_memory_api_get_entry_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer change-me-in-production"}
    resp = client.get("/api/v1/memory/missing-entry", headers=headers)
    assert resp.status_code == 404
