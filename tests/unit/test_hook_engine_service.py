from __future__ import annotations

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.domain.hooks.models import HookActionType, HookDefinition, HookEventType
from aetheros.domain.shared.exceptions import ConflictError, NotFoundError, ValidationError
from aetheros.domain.shared.value_objects import TenantId


def test_register_and_list_hooks() -> None:
    service = HookEngineService()
    hook = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="pre-run-check",
        event_type=HookEventType.PRE_AGENT_RUN,
        priority=10,
        action=HookActionType.CONTINUE,
    )

    registered = service.register_hook(hook)

    assert registered.id == hook.id
    assert registered.name == "pre-run-check"

    hooks = service.list_hooks(tenant_id=TenantId("tenant-1"))
    assert len(hooks) == 1
    assert hooks[0].tenant_id == TenantId("tenant-1")


def test_register_hook_rejects_empty_name() -> None:
    service = HookEngineService()
    hook = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="",
        event_type=HookEventType.PRE_AGENT_RUN,
    )

    try:
        service.register_hook(hook)
    except ValidationError as exc:
        assert "name" in str(exc).lower()
    else:
        raise AssertionError("Expected ValidationError")


def test_register_duplicate_hook_raises_conflict() -> None:
    service = HookEngineService()
    hook = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="pre-run-check",
        event_type=HookEventType.PRE_AGENT_RUN,
    )

    service.register_hook(hook)

    try:
        service.register_hook(hook)
    except ConflictError as exc:
        assert "already registered" in str(exc).lower()
    else:
        raise AssertionError("Expected ConflictError")


def test_get_hook_not_found_raises_not_found() -> None:
    service = HookEngineService()

    try:
        service.get_hook("missing")
    except NotFoundError as exc:
        assert "not found" in str(exc).lower()
    else:
        raise AssertionError("Expected NotFoundError")


def test_execute_hooks_orders_by_priority_and_continues() -> None:
    service = HookEngineService()
    hook_a = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="first",
        event_type=HookEventType.PRE_AGENT_RUN,
        priority=5,
        config={"step": 1},
    )
    hook_b = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="second",
        event_type=HookEventType.PRE_AGENT_RUN,
        priority=10,
        config={"step": 2},
    )

    service.register_hook(hook_a)
    service.register_hook(hook_b)

    output = service.execute_hooks(
        event_type=HookEventType.PRE_AGENT_RUN,
        payload={"input": "test"},
    )

    assert output["input"] == "test"
    assert output[f"hook_{hook_a.id}"] == {"step": 1}
    assert output[f"hook_{hook_b.id}"] == {"step": 2}


def test_execute_hooks_aborts_on_abort_action() -> None:
    service = HookEngineService()
    hook_abort = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="abort-hook",
        event_type=HookEventType.PRE_AGENT_RUN,
        priority=1,
        action=HookActionType.ABORT,
        config={"reason": "stop"},
    )
    hook_continue = HookDefinition(
        tenant_id=TenantId("tenant-1"),
        name="later-hook",
        event_type=HookEventType.PRE_AGENT_RUN,
        priority=10,
        config={"step": 2},
    )

    service.register_hook(hook_abort)
    service.register_hook(hook_continue)

    output = service.execute_hooks(
        event_type=HookEventType.PRE_AGENT_RUN,
        payload={"input": "test"},
    )

    assert output["hook_aborted"] is True
    assert output["aborted_hook_id"] == hook_abort.id
    assert f"hook_{hook_continue.id}" not in output
