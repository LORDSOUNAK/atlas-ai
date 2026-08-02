from __future__ import annotations

import pytest

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.domain.hooks.models import HookActionType, HookDefinition, HookEventType
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import WorkflowDefinition, WorkflowNode


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
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )

    service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))

    with pytest.raises(ConflictError):
        service.create_workflow(definition=definition, tenant_id=TenantId("tenant-1"))


def test_create_run_returns_workflow_run() -> None:
    service = WorkflowService()
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )
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
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )
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
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )
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
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )
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
    definition = WorkflowDefinition(
        name="demo",
        nodes=[
            WorkflowNode(id="start", type="START"),
            WorkflowNode(id="end", type="END"),
        ],
    )
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
