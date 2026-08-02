from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Dict, Any
from aetheros.application.langgraph.runtime_api import WorkflowRuntime, ExecutionChunk, ExecutionResult
from aetheros.application.langgraph.runtime_api import ExecutionChunk as _EC
from aetheros.application.langgraph.runtime_api import ExecutionResult as _ER
import asyncio


class LangGraphRuntime(WorkflowRuntime):
    """Minimal LangGraph runtime adapter (skeleton).

    This provides a small interface the rest of the app can call while the
    real LangGraph integration is developed. It implements:
    - `compile_graph(definition)` — compile a workflow definition into a state dict
    - `astream(graph_state, config)` — async generator yielding execution chunks
    - `interrupt(graph_id)` / `resume(graph_id, input)` — basic control hooks
    - `checkpoint(graph_id, state)` — placeholder hook that callers may await
    """

    def __init__(self) -> None:
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._interrupt_events: Dict[str, asyncio.Event] = {}

    def compile_graph(self, graph_id: str, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Compile a workflow definition into a runtime graph state.

        For now this stores a shallow copy of the definition and returns a
        simple state container the runtime executor can consume.
        """
        state = {
            "id": graph_id,
            "definition": dict(definition),
            "position": 0,
            "state_data": {},
        }
        self._graphs[graph_id] = state
        self._interrupt_events[graph_id] = asyncio.Event()
        return state

    def execute(self, graph_id: str, config: Dict[str, Any] | None = None) -> ExecutionResult:
        """Run the compiled graph synchronously by consuming the async stream.

        This is a convenience for tests and for simple runtimes. It will
        iterate the async stream to completion and gather outputs.
        """
        outputs: list[Dict[str, Any]] = []

        async def _drain():
            async for chunk in self.astream(graph_id, config=config):
                # normalize chunk dicts into outputs
                if chunk.get("event") == "node":
                    outputs.append(chunk.get("output") or {})

        # Run the async drain synchronously using asyncio.run
        asyncio.run(_drain())
        return ExecutionResult(graph_id=graph_id, status="COMPLETED", outputs=outputs)

    async def astream(self, graph_id: str, config: Dict[str, Any] | None = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Asynchronously execute the compiled graph, yielding partial results.

        This is a simple placeholder: it yields one "node result" per second.
        Real implementation will drive LangGraph StateGraph execution and yield
        LLM/streaming outputs as they are produced.
        """
        if graph_id not in self._graphs:
            raise KeyError(f"Graph {graph_id} not compiled")

        graph = self._graphs[graph_id]
        total_nodes = len(graph["definition"].get("nodes", []))
        # yield a start message
        yield {"graph_id": graph_id, "event": "start", "position": graph["position"]}

        while graph["position"] < total_nodes:
            # Respect interrupt: if interrupted, wait until resumed
            event = self._interrupt_events[graph_id]
            if event.is_set():
                # Pause until cleared by resume
                yield {"graph_id": graph_id, "event": "paused", "position": graph["position"]}
                await event.wait()

            # Simulate work on the current node
            await asyncio.sleep(0.2)
            node_idx = graph["position"]
            result = {"graph_id": graph_id, "event": "node", "node_index": node_idx, "output": {"text": f"output-{node_idx}"}}
            # Advance position
            graph["position"] += 1
            yield result

        yield {"graph_id": graph_id, "event": "complete", "position": graph["position"]}

    def interrupt(self, graph_id: str) -> None:
        """Signal that execution should be paused."""
        ev = self._interrupt_events.get(graph_id)
        if ev:
            ev.set()

    def resume(self, graph_id: str) -> None:
        """Resume a previously interrupted execution."""
        ev = self._interrupt_events.get(graph_id)
        if ev and ev.is_set():
            # Clear event and set a fresh one to allow future interrupts
            ev.clear()

    async def checkpoint(self, graph_id: str) -> Dict[str, Any]:
        """Return the current run state for persistence.

        Callers may await this before persisting to their storage layer.
        """
        if graph_id not in self._graphs:
            raise KeyError(graph_id)
        # Return a copy to avoid external mutation
        return dict(self._graphs[graph_id])
