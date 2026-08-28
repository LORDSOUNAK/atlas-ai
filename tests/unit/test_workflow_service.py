from __future__ import annotations

import pytest

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.domain.hooks.models import HookActionType, HookDefinition, HookEventType
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import WorkflowDefinition, WorkflowNode


def make_definition(name: str = "demo") -> WorkflowDefinition:
    return WorkflowDefinition(
        name=name,
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )


def test_create_workflow_requires_name() -> None:
    service = WorkflowService()

    with pytest.raises(ValidationError):
        service.create_workflow(
            definition=WorkflowDefinition(
                name="",
                nodes=[
                    WorkflowNode(id="start", type="START"),
                    WorkflowNode(id="end", type="END"),
                ],
            ),
            tenant_id=TenantId("tenant-1"),
        )


def test_create_workflow_rejects_duplicates() -> None:
    service = WorkflowService()
    definition = make_definition()

    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    with pytest.raises(ConflictError):
        service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))


def test_create_run_returns_workflow_run() -> None:
    service = WorkflowService()
    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    assert run.workflow_id == "demo"
    assert run.status == "RUNNING"


def test_invalid_workflow_structure_is_rejected() -> None:
    with pytest.raises(ValueError):
        WorkflowDefinition(
            name="invalid",
            nodes=[WorkflowNode(id="only", type="AGENT")],
        )


def test_run_can_be_paused_resumed_and_cancelled() -> None:
    service = WorkflowService()
    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    running_run = service.create_run("demo", tenant_id=TenantId("tenant-1"))
    paused_run = service.pause_run(running_run.id)
    resumed_run = service.resume_run(paused_run.id)
    cancelled_run = service.cancel_run(resumed_run.id)

    assert paused_run.status == "PAUSED"
    assert resumed_run.status == "RUNNING"
    assert cancelled_run.status == "CANCELLED"


def test_pre_pause_hook_aborts_pause_without_changing_status() -> None:
    hook_engine = HookEngineService()
    service = WorkflowService(hook_engine=hook_engine)
    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    hook_engine.register_hook(
        HookDefinition(
            tenant_id=TenantId("tenant-1"),
            name="abort-pause",
            event_type=HookEventType.PRE_WORKFLOW_PAUSE,
            priority=1,
            action=HookActionType.ABORT,
            config={"reason": "cannot pause"},
        )
    )

    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))
    paused_run = service.pause_run(run.id)

    assert paused_run.status == "RUNNING"
    assert paused_run.state["hook_aborted"] is True
    assert paused_run.state["aborted_hook_id"] is not None


def test_pre_workflow_run_hook_can_abort_run_creation() -> None:
    hook_engine = HookEngineService()
    service = WorkflowService(hook_engine=hook_engine)
    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    hook = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="abort-workflow",
        event_type=HookEventType.PRE_WORKFLOW_RUN,
        priority=1,
        action=HookActionType.ABORT,
        config={"reason": "blocked"},
    )
    hook_engine.register_hook(hook)

    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    assert run.status == "CANCELLED"
    assert run.state["hook_aborted"] is True
    assert run.state["aborted_hook_id"] == hook.id


def test_workflow_hooks_apply_only_for_matching_tenant() -> None:
    hook_engine = HookEngineService()
    service = WorkflowService(hook_engine=hook_engine)
    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    hook_engine.register_hook(
        HookDefinition(
            tenant_id=TenantId("tenant-2"),
            name="abort-other-tenant",
            event_type=HookEventType.PRE_WORKFLOW_RUN,
            priority=1,
            action=HookActionType.ABORT,
            config={"reason": "wrong tenant"},
        )
    )

    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    assert run.status == "RUNNING"
    assert run.state.get("hook_aborted") is None


def test_list_workflows_returns_all_definitions() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("wf-1"), tenant_id=TenantId("tenant-1")
    )
    service.create_workflow(
        definition=make_definition("wf-2"), tenant_id=TenantId("tenant-1")
    )

    workflows = service.list_workflows()

    assert len(workflows) == 2


def test_get_workflow_returns_existing_definition() -> None:
    service = WorkflowService()
    definition = make_definition("my-workflow")
    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    found = service.get_workflow("my-workflow")

    assert found.name == "my-workflow"


def test_get_workflow_raises_for_missing_definition() -> None:
    service = WorkflowService()

    with pytest.raises(NotFoundError, match="not found"):
        service.get_workflow("missing")


def test_delete_workflow_removes_definition() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("to-delete"), tenant_id=TenantId("tenant-1")
    )

    service.delete_workflow("to-delete")

    with pytest.raises(NotFoundError, match="not found"):
        service.get_workflow("to-delete")


def test_delete_workflow_raises_for_missing_definition() -> None:
    service = WorkflowService()

    with pytest.raises(NotFoundError, match="not found"):
        service.delete_workflow("missing")


def test_delete_workflow_rejects_with_active_runs() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("active"), tenant_id=TenantId("tenant-1")
    )
    service.create_run("active", tenant_id=TenantId("tenant-1"))

    with pytest.raises(ConflictError, match="active runs"):
        service.delete_workflow("active")


def test_get_run_returns_existing_run() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    found = service.get_run(run.id)

    assert found.id == run.id
    assert found.status == "RUNNING"


def test_get_run_raises_for_missing_run() -> None:
    service = WorkflowService()

    with pytest.raises(NotFoundError, match="not found"):
        service.get_run("missing-run")


def test_delete_run_removes_completed_run() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))
    service.cancel_run(run.id)

    service.delete_run(run.id)

    with pytest.raises(NotFoundError, match="not found"):
        service.get_run(run.id)


def test_delete_run_raises_for_missing_run() -> None:
    service = WorkflowService()

    with pytest.raises(NotFoundError, match="not found"):
        service.delete_run("missing-run")


def test_delete_run_rejects_running_run() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    with pytest.raises(ConflictError, match="running or paused"):
        service.delete_run(run.id)


def test_delete_run_rejects_paused_run() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))
    service.pause_run(run.id)

    with pytest.raises(ConflictError, match="running or paused"):
        service.delete_run(run.id)


def test_list_runs_filters_by_tenant() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    service.create_run("demo", tenant_id=TenantId("tenant-1"))
    service.create_run("demo", tenant_id=TenantId("tenant-2"))

    runs_t1 = service.list_runs(tenant_id=TenantId("tenant-1"))
    runs_t2 = service.list_runs(tenant_id=TenantId("tenant-2"))

    assert len(runs_t1) == 1
    assert len(runs_t2) == 1
    assert runs_t1[0].tenant_id == TenantId("tenant-1")
    assert runs_t2[0].tenant_id == TenantId("tenant-2")


def test_create_run_sets_started_at_timestamp() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )

    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    assert run.started_at is not None
    assert run.started_at.endswith("Z")


def test_cancel_run_sets_ended_at_timestamp() -> None:
    service = WorkflowService()
    service.create_workflow(
        definition=make_definition("demo"), tenant_id=TenantId("tenant-1")
    )
    run = service.create_run("demo", tenant_id=TenantId("tenant-1"))

    cancelled = service.cancel_run(run.id)

    assert cancelled.ended_at is not None
    assert cancelled.ended_at.endswith("Z")
