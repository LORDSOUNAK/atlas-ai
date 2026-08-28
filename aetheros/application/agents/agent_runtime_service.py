from __future__ import annotations

from typing import Any

from aetheros.domain.agents.models import Agent, AgentConfig, AgentSession, AgentStatus
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import (
    AgentId,
    SessionId,
    TenantId,
    utc_now_iso,
)


class AgentRuntimeService:
    """Manage agent lifecycle state transitions for the runtime."""

    def __init__(self) -> None:
        self._agents: dict[AgentId, Agent] = {}
        self._sessions: dict[SessionId, AgentSession] = {}

    def _next_timestamp(self) -> str:
        return utc_now_iso()

    def get_agent(self, agent_id: AgentId) -> Agent:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValidationError("Agent not found")
        return agent

    def get_session(self, session_id: SessionId) -> AgentSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValidationError("Session not found")
        return session

    def _get_agent(self, agent_id: AgentId) -> Agent:
        return self.get_agent(agent_id)

    def _get_session(self, session_id: SessionId) -> AgentSession:
        return self.get_session(session_id)

    def _set_agent_status(self, agent_id: AgentId, status: AgentStatus) -> None:
        agent = self._get_agent(agent_id)
        agent.status = status

    def _snapshot_session(self, session: AgentSession) -> AgentSession:
        return session.model_copy(deep=True)

    def create_agent(self, config: AgentConfig, tenant_id: TenantId) -> Agent:
        if not config.name:
            raise ValidationError("Agent name is required")
        if not config.model:
            raise ValidationError("Agent model is required")
        if not config.memory_scopes:
            raise ValidationError("At least one memory scope is required")

        agent = Agent(tenant_id=tenant_id, name=config.name, config=config)
        self._agents[agent.id] = agent
        return agent

    def start_agent(self, agent_id: AgentId) -> AgentSession:
        agent = self._get_agent(agent_id)
        if agent.status in {AgentStatus.RUNNING, AgentStatus.PAUSED}:
            raise ConflictError("Agent is already running or paused")
        if agent.status == AgentStatus.WAITING_FOR_HUMAN:
            raise ConflictError("Agent is awaiting human input")

        agent.status = AgentStatus.RUNNING
        session = AgentSession(
            agent_id=agent_id,
            tenant_id=agent.tenant_id,
            status=AgentStatus.RUNNING,
            started_at=self._next_timestamp(),
        )
        self._sessions[session.id] = session
        return self._snapshot_session(session)

    def stop_agent(self, session_id: SessionId) -> AgentSession:
        session = self._get_session(session_id)
        session.status = AgentStatus.CANCELLED
        session.ended_at = self._next_timestamp()
        self._set_agent_status(session.agent_id, AgentStatus.CANCELLED)
        return self._snapshot_session(session)

    def pause_agent(self, session_id: SessionId) -> AgentSession:
        session = self._get_session(session_id)
        if session.status != AgentStatus.RUNNING:
            raise ConflictError("Session is not running")

        session.status = AgentStatus.PAUSED
        self._set_agent_status(session.agent_id, AgentStatus.PAUSED)
        return self._snapshot_session(session)

    def resume_agent(self, session_id: SessionId) -> AgentSession:
        session = self._get_session(session_id)
        if session.status != AgentStatus.PAUSED:
            raise ConflictError("Session is not paused")

        session.status = AgentStatus.RUNNING
        self._set_agent_status(session.agent_id, AgentStatus.RUNNING)
        return self._snapshot_session(session)

    def inject_human_feedback(
        self, session_id: SessionId, feedback: dict[str, Any] | None = None
    ) -> AgentSession:
        session = self._get_session(session_id)
        if session.status != AgentStatus.WAITING_FOR_HUMAN:
            raise ConflictError("Session is not awaiting human input")

        session.input["human_feedback"] = feedback or {}
        session.status = AgentStatus.RUNNING
        self._set_agent_status(session.agent_id, AgentStatus.RUNNING)
        return self._snapshot_session(session)

    def delete_agent(self, agent_id: AgentId) -> None:
        agent = self._get_agent(agent_id)
        if agent.status in {AgentStatus.RUNNING, AgentStatus.PAUSED}:
            raise ConflictError("Cannot delete an agent that is running or paused")
        del self._agents[agent_id]

    def list_agents(
        self,
        tenant_id: TenantId,
        status: AgentStatus | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Agent]:
        if page < 1 or page_size < 1:
            raise ValidationError("Page and page size must be positive")

        agents = [
            agent
            for agent in self._agents.values()
            if agent.tenant_id == tenant_id
            and (status is None or agent.status == status)
        ]
        start = (page - 1) * page_size
        return agents[start : start + page_size]
