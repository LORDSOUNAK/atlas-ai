from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from aetheros.application.agents.agent_runtime_service import AgentRuntimeService
from aetheros.container import container
from aetheros.domain.agents.models import AgentConfig
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import AgentId, SessionId, TenantId

router = APIRouter(prefix="/agents", tags=["agents"])


def get_agent_runtime_service() -> AgentRuntimeService:
    return container.agent_runtime_service()


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


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        agent = service.get_agent(AgentId(agent_id))
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": agent.id, "name": agent.name, "status": agent.status.value}


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> None:
    try:
        service.delete_agent(AgentId(agent_id))
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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


@router.post("/{agent_id}/stop")
async def stop_agent(
    session_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.stop_agent(SessionId(session_id))
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "status": session.status.value}


@router.post("/{agent_id}/pause")
async def pause_agent(
    session_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.pause_agent(SessionId(session_id))
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "status": session.status.value}


@router.post("/{agent_id}/resume")
async def resume_agent(
    session_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.resume_agent(SessionId(session_id))
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "status": session.status.value}


@router.post("/{agent_id}/sessions/{session_id}/feedback")
async def inject_human_feedback(
    session_id: str,
    feedback: dict[str, Any] | None = None,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.inject_human_feedback(SessionId(session_id), feedback)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "status": session.status.value}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> dict[str, object]:
    try:
        session = service.get_session(SessionId(session_id))
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": session.id,
        "agent_id": session.agent_id,
        "status": session.status.value,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    }
