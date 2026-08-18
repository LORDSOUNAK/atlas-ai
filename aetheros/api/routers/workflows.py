from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.container import container
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import WorkflowDefinition, WorkflowRun

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service() -> WorkflowService:
    return container.workflow_service()


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


@router.get("", response_model=list[WorkflowRun])
async def list_runs(
    tenant_id: TenantId,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRun]:
    return service.list_runs(tenant_id=tenant_id)
