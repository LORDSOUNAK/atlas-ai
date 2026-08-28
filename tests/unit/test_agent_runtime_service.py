from __future__ import annotations

import pytest

from aetheros.application.agents.agent_runtime_service import AgentRuntimeService
from aetheros.domain.agents.models import AgentConfig, AgentStatus
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import TenantId


def test_create_agent_succeeds_with_valid_config() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o", memory_scopes=["SESSION"])

    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    assert agent.name == "planner"
    assert agent.tenant_id == TenantId("tenant-1")
    assert agent.status.value == "IDLE"


def test_create_agent_rejects_empty_name() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="", model="gpt-4o")

    try:
        service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    except ValidationError as exc:
        assert "name" in str(exc).lower()
    else:
        raise AssertionError("Expected ValidationError")


def test_start_agent_rejects_duplicate_run() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    service.start_agent(agent.id)

    try:
        service.start_agent(agent.id)
    except ConflictError as exc:
        assert "already running" in str(exc).lower()
    else:
        raise AssertionError("Expected ConflictError")


def test_stop_agent_marks_session_cancelled() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    session = service.start_agent(agent.id)

    stopped = service.stop_agent(session.id)

    assert stopped.status.value == "CANCELLED"
    assert stopped.ended_at is not None


def test_list_agents_filters_by_tenant() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    service.create_agent(config=config, tenant_id=TenantId("tenant-2"))

    agents = service.list_agents(TenantId("tenant-1"))

    assert len(agents) == 1
    assert agents[0].tenant_id == TenantId("tenant-1")


def test_completed_agent_can_be_restarted() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    session = service.start_agent(agent.id)
    service.stop_agent(session.id)

    restarted = service.start_agent(agent.id)

    assert restarted.status == AgentStatus.RUNNING
    assert agent.status == AgentStatus.RUNNING


def test_pause_and_resume_change_session_status() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    session = service.start_agent(agent.id)

    paused = service.pause_agent(session.id)
    resumed = service.resume_agent(session.id)

    assert paused.status == AgentStatus.PAUSED
    assert resumed.status == AgentStatus.RUNNING


def test_inject_human_feedback_resumes_waiting_session() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    session = service.start_agent(agent.id)
    service._sessions[session.id].status = AgentStatus.WAITING_FOR_HUMAN

    resumed = service.inject_human_feedback(session.id, {"text": "continue"})

    assert resumed.status == AgentStatus.RUNNING
    assert resumed.input["human_feedback"] == {"text": "continue"}


def test_list_agents_supports_status_filtering_and_pagination() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    agents = service.list_agents(
        TenantId("tenant-1"),
        status=AgentStatus.IDLE,
        page=1,
        page_size=1,
    )

    assert len(agents) == 1


def test_get_agent_returns_existing_agent() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    found = service.get_agent(agent.id)

    assert found.id == agent.id
    assert found.name == "planner"


def test_get_agent_raises_for_missing_agent() -> None:
    service = AgentRuntimeService()

    with pytest.raises(ValidationError, match="not found"):
        service.get_agent("missing-agent")


def test_get_session_returns_existing_session() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    session = service.start_agent(agent.id)

    found = service.get_session(session.id)

    assert found.id == session.id
    assert found.status == AgentStatus.RUNNING


def test_get_session_raises_for_missing_session() -> None:
    service = AgentRuntimeService()

    with pytest.raises(ValidationError, match="not found"):
        service.get_session("missing-session")


def test_delete_agent_removes_idle_agent() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))

    service.delete_agent(agent.id)

    with pytest.raises(ValidationError, match="not found"):
        service.get_agent(agent.id)


def test_delete_agent_rejects_running_agent() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    service.start_agent(agent.id)

    with pytest.raises(ConflictError, match="running or paused"):
        service.delete_agent(agent.id)


def test_delete_agent_rejects_paused_agent() -> None:
    service = AgentRuntimeService()
    config = AgentConfig(name="planner", model="gpt-4o")
    agent = service.create_agent(config=config, tenant_id=TenantId("tenant-1"))
    session = service.start_agent(agent.id)
    service.pause_agent(session.id)

    with pytest.raises(ConflictError, match="running or paused"):
        service.delete_agent(agent.id)


def test_delete_agent_raises_for_missing_agent() -> None:
    service = AgentRuntimeService()

    with pytest.raises(ValidationError, match="not found"):
        service.delete_agent("missing-agent")
