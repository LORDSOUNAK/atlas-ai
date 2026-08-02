from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from aetheros.domain.shared.value_objects import HookId, TenantId


class HookEventType(StrEnum):
    PRE_AGENT_RUN = "PRE_AGENT_RUN"
    POST_AGENT_RUN = "POST_AGENT_RUN"
    PRE_WORKFLOW_RUN = "PRE_WORKFLOW_RUN"
    POST_WORKFLOW_RUN = "POST_WORKFLOW_RUN"
    PRE_WORKFLOW_PAUSE = "PRE_WORKFLOW_PAUSE"
    POST_WORKFLOW_PAUSE = "POST_WORKFLOW_PAUSE"
    PRE_WORKFLOW_RESUME = "PRE_WORKFLOW_RESUME"
    POST_WORKFLOW_RESUME = "POST_WORKFLOW_RESUME"
    PRE_WORKFLOW_CANCEL = "PRE_WORKFLOW_CANCEL"
    POST_WORKFLOW_CANCEL = "POST_WORKFLOW_CANCEL"
    PRE_TOOL_CALL = "PRE_TOOL_CALL"
    POST_TOOL_CALL = "POST_TOOL_CALL"


class HookActionType(StrEnum):
    CONTINUE = "CONTINUE"
    ABORT = "ABORT"


class HookDefinition(BaseModel):
    id: HookId = Field(default_factory=lambda: HookId(str(uuid4())))
    tenant_id: TenantId
    name: str
    event_type: HookEventType
    priority: int = 100
    action: HookActionType = HookActionType.CONTINUE
    config: dict[str, Any] = Field(default_factory=dict)
