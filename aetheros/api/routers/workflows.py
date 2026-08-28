from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.container import container
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import WorkflowDefinition, WorkflowRun

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service() -> WorkflowService:
    return container.workflow_service()


# --- Run routes (registered before /{workflow_name} to avoid path conflicts) ---

@router.get("/runs", response_model=list[WorkflowRun])
async def list_runs(
    tenant_id: TenantId,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRun]:
    return service.list_runs(tenant_id=tenant_id)


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRun:
    try:
        return service.get_run(run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/runs/{run_id}", status_code=204)
async def delete_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    try:
        service.delete_run(run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/runs/{run_id}/pause")
async def pause_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRun:
    try:
        return service.pause_run(run_id)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/resume")
async def resume_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRun:
    try:
        return service.resume_run(run_id)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRun:
    try:
        return service.cancel_run(run_id)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/execute")
async def execute_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict[str, object]:
    try:
        result = service.execute_run_sync(run_id)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "graph_id": result.graph_id,
        "status": result.status,
        "outputs": result.outputs,
    }


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> StreamingResponse:
    """Stream execution chunks for a workflow run as Server-Sent Events."""

    async def event_stream():
        try:
            async for chunk in service.stream_run(run_id):
                yield f"data: {json.dumps(chunk)}\n\n"
        except ValidationError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- Workflow definition routes ---

@router.post("", status_code=201)
async def create_workflow(
    definition: WorkflowDefinition,
    tenant_id: TenantId,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinition:
    try:
        return service.create_workflow(definition=definition, tenant_id=tenant_id)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[WorkflowDefinition])
async def list_workflows(
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowDefinition]:
    return service.list_workflows()


@router.post("/{workflow_name}/runs", status_code=201)
async def create_run(
    workflow_name: str,
    tenant_id: TenantId,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRun:
    try:
        return service.create_run(workflow_name=workflow_name, tenant_id=tenant_id)
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workflow_name}")
async def get_workflow(
    workflow_name: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowDefinition:
    try:
        return service.get_workflow(workflow_name)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{workflow_name}", status_code=204)
async def delete_workflow(
    workflow_name: str,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    try:
        service.delete_workflow(workflow_name)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
