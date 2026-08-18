from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from aetheros.domain.shared.value_objects import (
    AgentId,
    SessionId,
    TenantId,
    utc_now_iso,
)


class AgentStatus(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"


class AgentConfig(BaseModel):
    name: str
    model: str
    memory_scopes: list[str] = Field(default_factory=lambda: ["SESSION"])
    timeout_seconds: int = 30
    max_iterations: int = 5
    context_window_tokens: int = 4000


class Agent(BaseModel):
    id: AgentId = Field(default_factory=lambda: AgentId(str(uuid4())))
    tenant_id: TenantId
    name: str
    config: AgentConfig
    status: AgentStatus = AgentStatus.IDLE
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class AgentSession(BaseModel):
    id: SessionId = Field(default_factory=lambda: SessionId(str(uuid4())))
    agent_id: AgentId
    tenant_id: TenantId
    status: AgentStatus = AgentStatus.RUNNING
    started_at: str = Field(default_factory=utc_now_iso)
    ended_at: str | None = None
    iteration_count: int = 0
    input: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    error: str | None = None
    trace_id: str | None = None
