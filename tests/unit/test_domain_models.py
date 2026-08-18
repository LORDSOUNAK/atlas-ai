from datetime import datetime

import pytest

from aetheros.domain.agents.models import Agent, AgentConfig, AgentSession, AgentStatus
from aetheros.domain.memory.models import MemoryEntry, MemoryScope
from aetheros.domain.shared.value_objects import utc_now_iso
from aetheros.domain.tenants.models import Tenant
from aetheros.domain.workflows.models import (
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)


def test_agent_config_accepts_valid_values() -> None:
    config = AgentConfig(name="planner", model="gpt-4o")

    assert config.name == "planner"
    assert config.model == "gpt-4o"


def test_agent_session_defaults_to_running() -> None:
    session = AgentSession(agent_id="agent-1", tenant_id="tenant-1")

    assert session.status == AgentStatus.RUNNING


def test_workflow_definition_requires_start_and_end_nodes() -> None:
    with pytest.raises(ValueError):
        WorkflowDefinition(
            name="demo",
            nodes=[WorkflowNode(id="n1", type="AGENT")],
            edges=[],
        )


def test_workflow_definition_validates_edges() -> None:
    workflow = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
        edges=[WorkflowEdge(id="e1", source="start", target="end")],
    )

    assert workflow.nodes[0].id == "start"


def test_tenant_defaults_to_free_tier() -> None:
    tenant = Tenant(id="tenant-1", name="Example")

    assert tenant.tier == "FREE"


def test_domain_models_generate_dynamic_utc_timestamps() -> None:
    ts = utc_now_iso()
    assert ts.endswith("Z")
    # Verify ISO-8601 parsing
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None

    agent = Agent(
        tenant_id="t1",
        name="a1",
        config=AgentConfig(name="a1", model="m1"),
    )
    assert agent.created_at.endswith("Z")
    assert agent.updated_at.endswith("Z")

    session = AgentSession(agent_id="a1", tenant_id="t1")
    assert session.started_at.endswith("Z")

    mem = MemoryEntry(tenant_id="t1", scope=MemoryScope.SESSION, key="k", value="v")
    assert mem.created_at.endswith("Z")
