from __future__ import annotations

from fastapi.testclient import TestClient

from aetheros.main import create_app


def _make_definition(name: str = "demo") -> dict[str, object]:
    return {
        "name": name,
        "nodes": [
            {"id": "start", "type": "START"},
            {"id": "end", "type": "END"},
        ],
        "edges": [{"id": "e1", "source": "start", "target": "end"}],
    }


def test_workflow_create_list_get_and_delete() -> None:
    app = create_app()
    client = TestClient(app)

    # Create
    create_resp = client.post(
        "/api/v1/workflows",
        json=_make_definition("wf-1"),
        params={"tenant_id": "tenant-1"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["name"] == "wf-1"

    # List
    list_resp = client.get("/api/v1/workflows")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get
    get_resp = client.get("/api/v1/workflows/wf-1")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "wf-1"

    # Delete
    del_resp = client.delete("/api/v1/workflows/wf-1")
    assert del_resp.status_code == 204

    # Verify deleted
    get_resp2 = client.get("/api/v1/workflows/wf-1")
    assert get_resp2.status_code == 404


def test_workflow_get_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/workflows/missing")
    assert response.status_code == 404


def test_workflow_delete_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.delete("/api/v1/workflows/missing")
    assert response.status_code == 404


def test_workflow_create_run_and_list_runs() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo"),
        params={"tenant_id": "tenant-1"},
    )

    create_run_resp = client.post(
        "/api/v1/workflows/demo/runs",
        params={"tenant_id": "tenant-1"},
    )
    assert create_run_resp.status_code == 201
    create_run_resp.json()["id"]
    assert create_run_resp.json()["status"] == "RUNNING"

    list_resp = client.get("/api/v1/workflows/runs", params={"tenant_id": "tenant-1"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_workflow_get_run_returns_existing_run() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo"),
        params={"tenant_id": "tenant-1"},
    )
    create_run_resp = client.post(
        "/api/v1/workflows/demo/runs",
        params={"tenant_id": "tenant-1"},
    )
    run_id = create_run_resp.json()["id"]

    response = client.get(f"/api/v1/workflows/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["id"] == run_id


def test_workflow_get_run_returns_404_for_missing() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/workflows/runs/missing-run")
    assert response.status_code == 404


def test_workflow_pause_resume_cancel_lifecycle() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo"),
        params={"tenant_id": "tenant-1"},
    )
    create_run_resp = client.post(
        "/api/v1/workflows/demo/runs",
        params={"tenant_id": "tenant-1"},
    )
    run_id = create_run_resp.json()["id"]

    # Pause
    pause_resp = client.post(f"/api/v1/workflows/runs/{run_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"

    # Resume
    resume_resp = client.post(f"/api/v1/workflows/runs/{run_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "RUNNING"

    # Cancel
    cancel_resp = client.post(f"/api/v1/workflows/runs/{run_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


def test_workflow_delete_run_after_completion() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo"),
        params={"tenant_id": "tenant-1"},
    )
    create_run_resp = client.post(
        "/api/v1/workflows/demo/runs",
        params={"tenant_id": "tenant-1"},
    )
    run_id = create_run_resp.json()["id"]
    client.post(f"/api/v1/workflows/runs/{run_id}/cancel")

    del_resp = client.delete(f"/api/v1/workflows/runs/{run_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/workflows/runs/{run_id}")
    assert get_resp.status_code == 404


def test_workflow_delete_run_rejects_running_run() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo"),
        params={"tenant_id": "tenant-1"},
    )
    create_run_resp = client.post(
        "/api/v1/workflows/demo/runs",
        params={"tenant_id": "tenant-1"},
    )
    run_id = create_run_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/workflows/runs/{run_id}")
    assert del_resp.status_code == 409


def test_workflow_list_runs_filters_by_tenant() -> None:
    app = create_app()
    client = TestClient(app)

    client.post(
        "/api/v1/workflows",
        json=_make_definition("demo-filter"),
        params={"tenant_id": "tenant-filter-t1"},
    )
    client.post(
        "/api/v1/workflows/demo-filter/runs",
        params={"tenant_id": "tenant-filter-t1"},
    )
    client.post(
        "/api/v1/workflows/demo-filter/runs",
        params={"tenant_id": "tenant-filter-t2"},
    )

    resp_t1 = client.get(
        "/api/v1/workflows/runs", params={"tenant_id": "tenant-filter-t1"}
    )
    resp_t2 = client.get(
        "/api/v1/workflows/runs", params={"tenant_id": "tenant-filter-t2"}
    )

    assert resp_t1.status_code == 200
    assert resp_t2.status_code == 200
    assert len(resp_t1.json()) == 1
    assert len(resp_t2.json()) == 1
