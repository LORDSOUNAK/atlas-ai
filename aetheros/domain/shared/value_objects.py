from __future__ import annotations

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
