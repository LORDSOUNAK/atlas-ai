from __future__ import annotations

from aetheros.application.tools.tool_registry_service import ToolRegistryService
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.tools.models import ToolDefinition, ToolSchema, ToolType


def test_register_and_retrieve_tool() -> None:
    service = ToolRegistryService()
    tool = ToolDefinition(
        tenant_id=TenantId("tenant-1"),
        name="weather",
        description="Fetch weather forecasts",
        tool_type=ToolType.EXTERNAL,
        tool_schema=ToolSchema(name="weather", description="Weather tool"),
    )

    registered = service.register_tool(tool)

    assert registered.id == tool.id
    assert registered.name == "weather"

    found = service.get_tool(registered.id)
    assert found.id == registered.id


def test_register_tool_rejects_missing_name() -> None:
    service = ToolRegistryService()
    tool = ToolDefinition(
        tenant_id=TenantId("tenant-1"),
        name="",
        tool_schema=ToolSchema(name="empty", description="No name"),
    )

    try:
        service.register_tool(tool)
    except ValidationError as exc:
        assert "name" in str(exc).lower()
    else:
        raise AssertionError("Expected ValidationError")


def test_register_duplicate_tool_raises_conflict() -> None:
    service = ToolRegistryService()
    tool = ToolDefinition(
        tenant_id=TenantId("tenant-1"),
        name="weather",
        tool_schema=ToolSchema(name="weather", description="Weather tool"),
    )

    service.register_tool(tool)

    try:
        service.register_tool(tool)
    except ConflictError as exc:
        assert "already registered" in str(exc).lower()
    else:
        raise AssertionError("Expected ConflictError")


def test_list_tools_filters_by_tenant() -> None:
    service = ToolRegistryService()
    tool_a = ToolDefinition(
        tenant_id=TenantId("tenant-1"),
        name="weather",
        tool_schema=ToolSchema(name="weather", description="Weather tool"),
    )
    tool_b = ToolDefinition(
        tenant_id=TenantId("tenant-2"),
        name="maps",
        tool_schema=ToolSchema(name="maps", description="Maps tool"),
    )

    service.register_tool(tool_a)
    service.register_tool(tool_b)

    tools = service.list_tools(tenant_id=TenantId("tenant-1"))

    assert len(tools) == 1
    assert tools[0].tenant_id == TenantId("tenant-1")


def test_get_tool_not_found_raises_not_found() -> None:
    service = ToolRegistryService()

    try:
        service.get_tool("missing")
    except NotFoundError as exc:
        assert "not found" in str(exc).lower()
    else:
        raise AssertionError("Expected NotFoundError")
