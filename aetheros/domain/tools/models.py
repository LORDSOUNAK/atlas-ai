from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from aetheros.domain.shared.value_objects import ToolId, TenantId


class ToolType(StrEnum):
    GENERIC = "GENERIC"
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"


class ToolSchema(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    id: ToolId = Field(default_factory=lambda: ToolId(str(uuid4())))
    tenant_id: TenantId
    name: str
    description: str | None = None
    tool_type: ToolType = ToolType.GENERIC
    tool_schema: ToolSchema
