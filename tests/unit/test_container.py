from __future__ import annotations

import os
from unittest import mock

from dependency_injector import containers

from aetheros.application.agents.agent_runtime_service import AgentRuntimeService
from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.langgraph.langgraph_runtime import LangGraphRuntime
from aetheros.application.memory.memory_service import MemoryService
from aetheros.application.tools.tool_registry_service import ToolRegistryService
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.config.settings import load_settings
from aetheros.container import Container
from aetheros.container import container as global_container


@mock.patch.dict(os.environ, {}, clear=True)
def test_container_initializes_with_defaults() -> None:
    container = Container()
    settings = container.config()

    assert settings.app_name == "aetheros"
    assert settings.app_env == "development"
    assert settings.debug is False


@mock.patch.dict(os.environ, {}, clear=True)
def test_container_exposes_settings_provider() -> None:
    container = Container()
    settings = container.settings()

    assert isinstance(settings, type(load_settings()))
    assert settings.app_name == "aetheros"


def test_container_exposes_service_singletons() -> None:
    container = Container()

    agent_svc_1 = container.agent_runtime_service()
    agent_svc_2 = container.agent_runtime_service()
    assert isinstance(agent_svc_1, AgentRuntimeService)
    assert agent_svc_1 is agent_svc_2

    hook_svc_1 = container.hook_engine_service()
    hook_svc_2 = container.hook_engine_service()
    assert isinstance(hook_svc_1, HookEngineService)
    assert hook_svc_1 is hook_svc_2

    langgraph_1 = container.langgraph_runtime()
    langgraph_2 = container.langgraph_runtime()
    assert isinstance(langgraph_1, LangGraphRuntime)
    assert langgraph_1 is langgraph_2

    workflow_svc_1 = container.workflow_service()
    workflow_svc_2 = container.workflow_service()
    assert isinstance(workflow_svc_1, WorkflowService)
    assert workflow_svc_1 is workflow_svc_2
    assert workflow_svc_1._hook_engine is hook_svc_1
    assert workflow_svc_1._workflow_runtime is langgraph_1

    mem_svc_1 = container.memory_service()
    mem_svc_2 = container.memory_service()
    assert isinstance(mem_svc_1, MemoryService)
    assert mem_svc_1 is mem_svc_2

    tool_svc_1 = container.tool_registry_service()
    tool_svc_2 = container.tool_registry_service()
    assert isinstance(tool_svc_1, ToolRegistryService)
    assert tool_svc_1 is tool_svc_2


def test_global_container_instance_is_available() -> None:
    assert isinstance(global_container, containers.Container)
    assert isinstance(global_container.agent_runtime_service(), AgentRuntimeService)
