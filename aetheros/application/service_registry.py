from __future__ import annotations

from aetheros.container import container

hook_engine_service = container.hook_engine_service()
langgraph_runtime = container.langgraph_runtime()
workflow_service = container.workflow_service()
memory_service = container.memory_service()
tool_registry_service = container.tool_registry_service()
agent_runtime_service = container.agent_runtime_service()
