# Runtime Interface

This file documents the new `WorkflowRuntime` abstraction introduced to decouple the workflow execution engine from `WorkflowService`.

Key points:

- `WorkflowRuntime` (in `aetheros.application.langgraph.runtime_api`) defines:
  - `compile_graph(graph_id, definition)` — compile a workflow definition into a runtime state.
  - `execute(graph_id, config=None)` — synchronous execution returning `ExecutionResult`.
  - `astream(graph_id, config=None)` — async generator yielding `ExecutionChunk` items.
  - `interrupt(graph_id)` / `resume(graph_id)` — control operations for human-in-the-loop or pause/resume.
  - `checkpoint(graph_id)` — return serializable run state for persistence.

- `LangGraphRuntime` implements `WorkflowRuntime` as a thin adapter and is registered as a singleton in `aetheros.application.service_registry`.

- `WorkflowService` now accepts an optional `workflow_runtime: WorkflowRuntime` dependency and uses only the abstract API. This keeps business logic out of FastAPI routes and allows swapping runtimes or mocking for tests.

- Future features (checkpoint persistence, retries, human approval) should be implemented inside runtime implementations or via additional services that interact through the runtime abstraction. No changes to `WorkflowService` are required to add those capabilities.
