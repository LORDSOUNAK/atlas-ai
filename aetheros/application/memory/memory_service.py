from __future__ import annotations

from typing import Any

from aetheros.domain.memory.models import MemoryEntry, MemoryScope
from aetheros.domain.shared.exceptions import NotFoundError, ValidationError
from aetheros.domain.shared.value_objects import MemoryEntryId, TenantId


class MemoryService:
    """Store and retrieve memory entries in scoped collections."""

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def create_entry(
        self,
        tenant_id: TenantId,
        scope: MemoryScope,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        if not key:
            raise ValidationError("Memory entry key is required")
        if value is None:
            raise ValidationError("Memory entry value cannot be null")

        entry = MemoryEntry(
            tenant_id=tenant_id,
            scope=scope,
            key=key,
            value=value,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    def get_entry(self, entry_id: MemoryEntryId) -> MemoryEntry:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        raise NotFoundError("Memory entry not found")

    def get_entries(
        self,
        tenant_id: TenantId,
        scope: MemoryScope | None = None,
        key: str | None = None,
    ) -> list[MemoryEntry]:
        results = [
            entry
            for entry in self._entries
            if entry.tenant_id == tenant_id
            and (scope is None or entry.scope == scope)
            and (key is None or entry.key == key)
        ]
        return results

    def clear_entries(
        self, tenant_id: TenantId, scope: MemoryScope | None = None
    ) -> int:
        before = len(self._entries)
        self._entries = [
            entry
            for entry in self._entries
            if not (
                entry.tenant_id == tenant_id
                and (scope is None or entry.scope == scope)
            )
        ]
        return before - len(self._entries)
