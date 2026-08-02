from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List


@dataclass
class ExecutionChunk:
    graph_id: str
    event: str
    position: int | None = None
    node_index: int | None = None
    output: Dict[str, Any] | None = None


@dataclass
class ExecutionResult:
    graph_id: str
    status: str
    outputs: List[Dict[str, Any]]
    metadata: Dict[str, Any] | None = None


class WorkflowRuntime(abc.ABC):
    """Abstract runtime interface for executing compiled workflow graphs."""

    @abc.abstractmethod
    def compile_graph(self, graph_id: str, definition: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def execute(self, graph_id: str, config: Dict[str, Any] | None = None) -> ExecutionResult:
        """Synchronous execution that runs to completion and returns an ExecutionResult."""
        pass

    @abc.abstractmethod
    async def astream(self, graph_id: str, config: Dict[str, Any] | None = None) -> AsyncGenerator[ExecutionChunk, None]:
        """Asynchronous stream of execution chunks for the given compiled graph."""
        pass

    @abc.abstractmethod
    def interrupt(self, graph_id: str) -> None:
        pass

    @abc.abstractmethod
    def resume(self, graph_id: str) -> None:
        pass

    @abc.abstractmethod
    async def checkpoint(self, graph_id: str) -> Dict[str, Any]:
        pass
