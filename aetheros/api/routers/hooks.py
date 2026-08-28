from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.container import container
from aetheros.domain.hooks.models import HookDefinition, HookEventType
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId

router = APIRouter(prefix="/hooks", tags=["hooks"])


def get_hook_engine_service() -> HookEngineService:
    return container.hook_engine_service()


@router.post("", status_code=201)
async def create_hook(
    hook: HookDefinition,
    tenant_id: TenantId,
    service: HookEngineService = Depends(get_hook_engine_service),
) -> HookDefinition:
    try:
        return service.register_hook(hook)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[HookDefinition])
async def list_hooks(
    tenant_id: TenantId | None = None,
    service: HookEngineService = Depends(get_hook_engine_service),
) -> list[HookDefinition]:
    return service.list_hooks(tenant_id=tenant_id)


@router.get("/{hook_id}")
async def get_hook(
    hook_id: str,
    service: HookEngineService = Depends(get_hook_engine_service),
) -> HookDefinition:
    try:
        return service.get_hook(hook_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{hook_id}", status_code=204)
async def delete_hook(
    hook_id: str,
    service: HookEngineService = Depends(get_hook_engine_service),
) -> None:
    try:
        service.delete_hook(hook_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/execute")
async def execute_hooks(
    event_type: HookEventType,
    tenant_id: TenantId,
    payload: dict[str, object] = Body(default_factory=dict),
    service: HookEngineService = Depends(get_hook_engine_service),
) -> dict[str, object]:
    return service.execute_hooks(
        event_type=event_type,
        payload=payload,
        tenant_id=tenant_id,
    )
