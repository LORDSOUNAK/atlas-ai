from __future__ import annotations


class AetherOSError(Exception):
    """Base error for the AetherOS platform."""


class DomainError(AetherOSError):
    """Domain-level validation or business-rule violation."""


class ValidationError(DomainError):
    """Raised when input data does not satisfy business rules."""


class NotFoundError(DomainError):
    """Raised when an entity cannot be located."""


class ConflictError(DomainError):
    """Raised when the requested state conflicts with current state."""


class AgentError(DomainError):
    """Base error for agent runtime operations."""


class AgentRunAbortedError(AgentError):
    """Raised when a pre-run hook aborts an agent session."""


class AgentTimeoutError(AgentError):
    """Raised when an agent exceeds its timeout budget."""


class ToolError(DomainError):
    """Base error for tool execution failures."""


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""


class HookAbortError(DomainError):
    """Raised when a hook aborts the chain."""
