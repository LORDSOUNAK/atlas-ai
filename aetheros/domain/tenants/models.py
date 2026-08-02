from __future__ import annotations

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: str
    name: str
    tier: str = "FREE"
    metadata: dict[str, object] = Field(default_factory=dict)
