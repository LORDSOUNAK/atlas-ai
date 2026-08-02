from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from aetheros.application.agents.agent_runtime_service import AgentRuntimeService
from aetheros.domain.agents.models import AgentConfig
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import AgentId, TenantId

router = APIRouter(prefix="/agents", tags=["agents"])


def get_agent_runtime_service() -> AgentRuntimeService:
    return AgentRuntimeService()


@router.post("", status_code=201)
async def create_agent(
    config: AgentConfig,
    tenant_id: TenantId,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        agent = service.create_agent(config=config, tenant_id=tenant_id)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": agent.id, "name": agent.name, "status": agent.status.value}


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.start_agent(AgentId(agent_id))
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "status": session.status.value}


@router.get("", response_model=list[dict[str, object]])
async def list_agents(
    tenant_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> list[dict[str, object]]:
    agents = service.list_agents(TenantId(tenant_id))
    return [
        {"id": agent.id, "name": agent.name, "status": agent.status.value}
        for agent in agents
    ]
