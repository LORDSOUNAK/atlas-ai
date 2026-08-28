from __future__ import annotations

from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.tools.models import ToolDefinition


class ToolRegistryService:
    """Register tools and validate tool definitions for the platform."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register_tool(self, tool: ToolDefinition) -> ToolDefinition:
        if not tool.name:
            raise ValidationError("Tool name is required")
        if tool.id in self._tools:
            raise ConflictError("Tool already registered")

        self._tools[tool.id] = tool
        return tool

    def get_tool(self, tool_id: str) -> ToolDefinition:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise NotFoundError("Tool not found")
        return tool

    def get_tool_by_name(
        self, name: str, tenant_id: TenantId | None = None
    ) -> ToolDefinition:
        for tool in self._tools.values():
            if tool.name == name and (
                tenant_id is None or tool.tenant_id == tenant_id
            ):
                return tool
        raise NotFoundError("Tool not found")

    def list_tools(self, tenant_id: TenantId | None = None) -> list[ToolDefinition]:
        return [
            tool
            for tool in self._tools.values()
            if tenant_id is None or tool.tenant_id == tenant_id
        ]

    def delete_tool(self, tool_id: str) -> None:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise NotFoundError("Tool not found")
        del self._tools[tool_id]
