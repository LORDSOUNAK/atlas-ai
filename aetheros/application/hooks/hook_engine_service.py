from __future__ import annotations

from typing import Any

from aetheros.domain.hooks.models import HookActionType, HookDefinition, HookEventType
from aetheros.domain.shared.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from aetheros.domain.shared.value_objects import TenantId


class HookEngineService:
    """Register and execute ordered hooks for defined events."""

    def __init__(self) -> None:
        self._hooks: dict[str, HookDefinition] = {}

    def register_hook(self, hook: HookDefinition) -> HookDefinition:
        if not hook.name:
            raise ValidationError("Hook name is required")
        if hook.id in self._hooks:
            raise ConflictError("Hook already registered")

        self._hooks[hook.id] = hook
        return hook

    def get_hook(self, hook_id: str) -> HookDefinition:
        hook = self._hooks.get(hook_id)
        if hook is None:
            raise NotFoundError("Hook not found")
        return hook

    def list_hooks(self, tenant_id: TenantId | None = None) -> list[HookDefinition]:
        return [
            hook
            for hook in self._hooks.values()
            if tenant_id is None or hook.tenant_id == tenant_id
        ]

    def execute_hooks(
        self,
        event_type: HookEventType,
        payload: dict[str, Any],
        tenant_id: TenantId | None = None,
    ) -> dict[str, Any]:
        applicable = sorted(
            (
                hook
                for hook in self._hooks.values()
                if hook.event_type == event_type
                and (tenant_id is None or hook.tenant_id == tenant_id)
            ),
            key=lambda hook: hook.priority,
        )

        output = payload.copy()
        for hook in applicable:
            if hook.action == HookActionType.ABORT:
                output["hook_aborted"] = True
                output["aborted_hook_id"] = hook.id
                return output
            output[f"hook_{hook.id}"] = hook.config

        return output
