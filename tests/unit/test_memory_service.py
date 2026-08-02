from __future__ import annotations

from aetheros.application.memory.memory_service import MemoryService
from aetheros.domain.memory.models import MemoryEntry, MemoryScope
from aetheros.domain.shared.exceptions import ValidationError
from aetheros.domain.shared.value_objects import TenantId


def test_create_memory_entry_and_retrieve_by_scope() -> None:
    service = MemoryService()

    entry = service.create_entry(
        tenant_id=TenantId("tenant-1"),
        scope=MemoryScope.SESSION,
        key="user_intent",
        value="remember this",
    )

    assert isinstance(entry, MemoryEntry)
    assert entry.scope == MemoryScope.SESSION
    assert entry.key == "user_intent"

    entries = service.get_entries(tenant_id=TenantId("tenant-1"), scope=MemoryScope.SESSION)

    assert len(entries) == 1
    assert entries[0].id == entry.id


def test_create_memory_entry_rejects_empty_key() -> None:
    service = MemoryService()

    try:
        service.create_entry(
            tenant_id=TenantId("tenant-1"),
            scope=MemoryScope.TENANT,
            key="",
            value="value",
        )
    except ValidationError as exc:
        assert "key" in str(exc).lower()
    else:
        raise AssertionError("Expected ValidationError")


def test_get_entries_filters_by_key_and_scope() -> None:
    service = MemoryService()
    tenant = TenantId("tenant-1")

    service.create_entry(tenant_id=tenant, scope=MemoryScope.SESSION, key="a", value=1)
    service.create_entry(tenant_id=tenant, scope=MemoryScope.SESSION, key="b", value=2)
    service.create_entry(tenant_id=tenant, scope=MemoryScope.TENANT, key="a", value=3)

    entries = service.get_entries(tenant_id=tenant, scope=MemoryScope.SESSION, key="a")

    assert len(entries) == 1
    assert entries[0].value == 1


def test_clear_entries_removes_matching_scope_entries() -> None:
    service = MemoryService()
    tenant = TenantId("tenant-1")

    service.create_entry(tenant_id=tenant, scope=MemoryScope.SESSION, key="x", value=1)
    service.create_entry(tenant_id=tenant, scope=MemoryScope.TENANT, key="y", value=2)

    removed = service.clear_entries(tenant_id=tenant, scope=MemoryScope.SESSION)

    assert removed == 1
    remaining = service.get_entries(tenant_id=tenant)
    assert len(remaining) == 1
    assert remaining[0].scope == MemoryScope.TENANT
