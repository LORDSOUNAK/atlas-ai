# AetherOS Foundation

This workspace contains the initial foundation for the AetherOS platform.

## Included in this implementation

- A Python package scaffold for the backend application
- Configuration loading with pydantic-settings
- A dependency injection container for wiring services and infrastructure components
- A simple FastAPI application entrypoint
- Agent runtime lifecycle support with create, start, stop, pause, resume, and human-feedback handling
- Workflow management with create, list, get, delete, pause, resume, cancel, and execute operations
- Hook engine for registering and executing ordered hooks on lifecycle events
- Memory service for scoped key-value storage
- Tool registry for registering and looking up tools by ID or name
- LangGraph runtime adapter with synchronous execution and async streaming
- Server-Sent Events (SSE) streaming endpoint for workflow execution
- Unit tests for configuration loading, container initialization, agent lifecycle behavior, workflow management, hook engine, memory service, tool registry, and all API endpoints
- Integration tests for workflow runtime execution with mock runtimes

## API Endpoints

### Agents (`/api/v1/agents`)
- `POST /` — Create an agent
- `GET /` — List agents (filtered by tenant)
- `GET /{agent_id}` — Get an agent
- `DELETE /{agent_id}` — Delete an agent (only if not running/paused)
- `POST /{agent_id}/start` — Start an agent session
- `POST /{agent_id}/stop` — Stop an agent session
- `POST /{agent_id}/pause` — Pause an agent session
- `POST /{agent_id}/resume` — Resume a paused agent session
- `POST /{agent_id}/sessions/{session_id}/feedback` — Inject human feedback
- `GET /sessions/{session_id}` — Get a session

### Workflows (`/api/v1/workflows`)
- `POST /` — Create a workflow definition
- `GET /` — List all workflow definitions
- `GET /{workflow_name}` — Get a workflow definition
- `DELETE /{workflow_name}` — Delete a workflow (only if no active runs)
- `POST /{workflow_name}/runs` — Create a workflow run
- `GET /runs` — List runs (filtered by tenant)
- `GET /runs/{run_id}` — Get a run
- `DELETE /runs/{run_id}` — Delete a run (only if not running/paused)
- `POST /runs/{run_id}/pause` — Pause a run
- `POST /runs/{run_id}/resume` — Resume a run
- `POST /runs/{run_id}/cancel` — Cancel a run
- `POST /runs/{run_id}/execute` — Execute a run synchronously
- `GET /runs/{run_id}/stream` — Stream execution chunks (SSE)

### Hooks (`/api/v1/hooks`)
- `POST /` — Register a hook
- `GET /` — List hooks (filtered by tenant)
- `GET /{hook_id}` — Get a hook
- `DELETE /{hook_id}` — Delete a hook
- `POST /execute` — Execute hooks for an event type

### Memory (`/api/v1/memory`)
- `POST /` — Create a memory entry
- `GET /` — List memory entries (filtered by tenant, scope, key)
- `GET /{entry_id}` — Get a memory entry
- `DELETE /` — Clear memory entries (filtered by tenant, scope)

### Tools (`/api/v1/tools`)
- `POST /` — Register a tool
- `GET /` — List tools (filtered by tenant)
- `GET /{tool_id}` — Get a tool
- `GET /name/{tool_name}` — Get a tool by name
- `DELETE /{tool_id}` — Delete a tool

### Health
- `GET /health` — Health check

## Development commands

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
black --check .
mypy aetheros
```
