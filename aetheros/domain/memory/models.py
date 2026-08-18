from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from aetheros.domain.shared.value_objects import (
    MemoryEntryId,
    TenantId,
    utc_now_iso,
)


class MemoryScope(StrEnum):
    SESSION = "SESSION"
    WORKFLOW = "WORKFLOW"
    TENANT = "TENANT"
    GLOBAL = "GLOBAL"


class MemoryEntry(BaseModel):
    id: MemoryEntryId = Field(default_factory=lambda: MemoryEntryId(str(uuid4())))
    tenant_id: TenantId
    scope: MemoryScope
    key: str
    value: Any
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)
