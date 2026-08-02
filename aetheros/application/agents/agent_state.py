from __future__ import annotations

from typing import Any, TypedDict, NotRequired


class AgentState(TypedDict, total=False):
    """Strongly typed runtime state for AetherOS agent execution.

    The structure is intentionally serializable so it can be checkpointed and
    later rehydrated without requiring custom schema logic.
    """

    messages: list[dict[str, Any]]
    current_task: str | None
    workflow_id: str | None
    execution_id: str | None
    active_node: str | None
    next_node: str | None
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    memory: dict[str, Any]
    context: dict[str, Any]
    variables: dict[str, Any]
    metadata: dict[str, Any]
    execution_status: str
    retry_count: int
    errors: list[str]
    trace_id: str | None
    user_id: str | None
    session_id: str | None


def create_empty_state() -> AgentState:
    """Create a new, serializable state with defaults for all fields."""
    return {
        "messages": [],
        "current_task": None,
        "workflow_id": None,
        "execution_id": None,
        "active_node": None,
        "next_node": None,
        "tool_calls": [],
        "tool_results": [],
        "memory": {},
        "context": {},
        "variables": {},
        "metadata": {},
        "execution_status": "IDLE",
        "retry_count": 0,
        "errors": [],
        "trace_id": None,
        "user_id": None,
        "session_id": None,
    }


def append_message(state: AgentState, message: dict[str, Any]) -> AgentState:
    """Append a message to the state and return a new state mapping."""
    new_state = dict(state)
    new_state["messages"] = list(state.get("messages", [])) + [message]
    return new_state


def set_active_node(state: AgentState, node_id: str | None) -> AgentState:
    new_state = dict(state)
    new_state["active_node"] = node_id
    return new_state


def set_next_node(state: AgentState, node_id: str | None) -> AgentState:
    new_state = dict(state)
    new_state["next_node"] = node_id
    return new_state


def update_variables(state: AgentState, updates: dict[str, Any]) -> AgentState:
    new_state = dict(state)
    new_state["variables"] = dict(state.get("variables", {}))
    new_state["variables"].update(updates)
    return new_state


def add_tool_result(state: AgentState, tool_result: dict[str, Any]) -> AgentState:
    new_state = dict(state)
    new_state["tool_results"] = list(state.get("tool_results", [])) + [tool_result]
    return new_state


def record_error(state: AgentState, error: str) -> AgentState:
    new_state = dict(state)
    new_state["errors"] = list(state.get("errors", [])) + [error]
    return new_state


def set_execution_status(state: AgentState, status: str) -> AgentState:
    new_state = dict(state)
    new_state["execution_status"] = status
    return new_state


def increment_retry_count(state: AgentState) -> AgentState:
    new_state = dict(state)
    new_state["retry_count"] = int(state.get("retry_count", 0)) + 1
    return new_state
