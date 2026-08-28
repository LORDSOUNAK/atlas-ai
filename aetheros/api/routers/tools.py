from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from aetheros.api.dependencies.auth import require_api_auth
from aetheros.application.tools.tool_registry_service import ToolRegistryService
from aetheros.container import container
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.tools.models import ToolDefinition

router = APIRouter(
    prefix="/tools",
    tags=["tools"],
    dependencies=[Depends(require_api_auth)],
)


def get_tool_registry_service() -> ToolRegistryService:
    return container.tool_registry_service()


@router.post("", status_code=201)
async def register_tool(
    tool: ToolDefinition,
    tenant_id: TenantId,
    service: ToolRegistryService = Depends(get_tool_registry_service),
) -> ToolDefinition:
    try:
        return service.register_tool(tool)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[ToolDefinition])
async def list_tools(
    tenant_id: TenantId | None = None,
    service: ToolRegistryService = Depends(get_tool_registry_service),
) -> list[ToolDefinition]:
    return service.list_tools(tenant_id=tenant_id)


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
) -> ToolDefinition:
    try:
        return service.get_tool(tool_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/name/{tool_name}")
async def get_tool_by_name(
    tool_name: str,
    tenant_id: TenantId | None = None,
    service: ToolRegistryService = Depends(get_tool_registry_service),
) -> ToolDefinition:
    try:
        return service.get_tool_by_name(tool_name, tenant_id=tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_tool_registry_service),
) -> None:
    try:
        service.delete_tool(tool_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
