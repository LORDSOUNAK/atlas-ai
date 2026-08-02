from __future__ import annotations

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.application.memory.memory_service import MemoryService
from aetheros.application.tools.tool_registry_service import ToolRegistryService
from aetheros.application.langgraph.langgraph_runtime import LangGraphRuntime

hook_engine_service = HookEngineService()
langgraph_runtime = LangGraphRuntime()
workflow_service = WorkflowService(hook_engine=hook_engine_service, workflow_runtime=langgraph_runtime)
memory_service = MemoryService()
tool_registry_service = ToolRegistryService()
