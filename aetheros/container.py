from __future__ import annotations

from dependency_injector import containers, providers

from aetheros.application.agents.agent_runtime_service import AgentRuntimeService
from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.langgraph.langgraph_runtime import LangGraphRuntime
from aetheros.application.memory.memory_service import MemoryService
from aetheros.application.tools.tool_registry_service import ToolRegistryService
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.config.settings import Settings, load_settings


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the AetherOS foundation package."""

    config = providers.Resource(load_settings)
    settings = providers.Singleton(Settings)

    hook_engine_service = providers.Singleton(HookEngineService)
    langgraph_runtime = providers.Singleton(LangGraphRuntime)
    workflow_service = providers.Singleton(
        WorkflowService,
        hook_engine=hook_engine_service,
        workflow_runtime=langgraph_runtime,
    )
    memory_service = providers.Singleton(MemoryService)
    tool_registry_service = providers.Singleton(ToolRegistryService)
    agent_runtime_service = providers.Singleton(AgentRuntimeService)

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.config()  # Trigger initialization so misconfiguration fails early.


container = Container()
