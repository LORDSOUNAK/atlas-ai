from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from aetheros.api.dependencies.auth import require_api_auth
from aetheros.application.memory.memory_service import MemoryService
from aetheros.container import container
from aetheros.domain.memory.models import MemoryEntry, MemoryScope
from aetheros.domain.shared.exceptions import NotFoundError, ValidationError
from aetheros.domain.shared.value_objects import MemoryEntryId, TenantId

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    dependencies=[Depends(require_api_auth)],
)


def get_memory_service() -> MemoryService:
    return container.memory_service()


@router.post("", status_code=201)
async def create_entry(
    tenant_id: TenantId,
    scope: MemoryScope,
    key: str,
    value: object,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryEntry:
    try:
        return service.create_entry(
            tenant_id=tenant_id, scope=scope, key=key, value=value
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[MemoryEntry])
async def list_entries(
    tenant_id: TenantId,
    scope: MemoryScope | None = None,
    key: str | None = None,
    service: MemoryService = Depends(get_memory_service),
) -> list[MemoryEntry]:
    return service.get_entries(tenant_id=tenant_id, scope=scope, key=key)


@router.get("/{entry_id}")
async def get_entry(
    entry_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryEntry:
    try:
        return service.get_entry(MemoryEntryId(entry_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("")
async def clear_entries(
    tenant_id: TenantId,
    scope: MemoryScope | None = None,
    service: MemoryService = Depends(get_memory_service),
) -> dict[str, int]:
    removed = service.clear_entries(tenant_id=tenant_id, scope=scope)
    return {"removed": removed}
