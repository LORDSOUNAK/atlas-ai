from __future__ import annotations

from datetime import UTC, datetime
from typing import NewType

AgentId = NewType("AgentId", str)
TenantId = NewType("TenantId", str)
SessionId = NewType("SessionId", str)
WorkflowId = NewType("WorkflowId", str)
RunId = NewType("RunId", str)
MemoryEntryId = NewType("MemoryEntryId", str)
ToolId = NewType("ToolId", str)
PluginId = NewType("PluginId", str)
HookId = NewType("HookId", str)


def utc_now_iso() -> str:
    """Generate a current ISO-8601 UTC timestamp string ending in 'Z'."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
