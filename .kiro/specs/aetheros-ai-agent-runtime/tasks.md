# Implementation Plan: AetherOS — AI Agent Runtime Platform

## Overview

This plan converts the AetherOS design into incremental coding tasks organized by the seven-phase
roadmap. Each task builds on previous ones and wires into the growing codebase. The implementation
uses Python 3.13 (async/await throughout), FastAPI, SQLAlchemy + asyncpg, Redis, LangGraph, and
the full observability stack defined in the design.

---

## Tasks

- [ ] 1. Project scaffold, configuration, and DI container
  - [ ] 1.1 Initialize Python project structure with pyproject.toml and all declared dependencies
    - Create `aetheros/` package layout matching design section 15.2
    - Configure `ruff`, `black`, and `mypy` in `pyproject.toml`
    - Add `pytest`, `pytest-asyncio`, and `hypothesis` to dev dependencies
    - _Requirements: 22.1, 24.3_
  - [ ] 1.2 Implement pydantic-settings `Settings` class and environment variable loading
    - Define all required config values (DB URL, Redis URL, JWT secret, Langfuse keys, etc.)
    - Validate that missing required values raise an error at startup
    - _Requirements: 22.3, 19.4_
  - [ ] 1.3 Implement `Container` class using `dependency-injector` to wire the full object graph
    - Wire all application services, repositories, and infrastructure adapters
    - Container must refuse to reach partially-initialized state on missing config
    - _Requirements: 22.1, 22.2, 22.3_
  - [ ]* 1.4 Write property test for Container initialization invariant
    - **Property: Container initialized with incomplete config must raise before accepting requests**
    - **Validates: Requirements 22.3**

- [ ] 2. Domain models, value objects, and exception hierarchy
  - [ ] 2.1 Implement all value objects and domain entities from design section 4
    - `AgentId`, `TenantId`, `SessionId`, `WorkflowId`, `RunId`, `MemoryEntryId`, `ToolId`, `PluginId`, `HookId`, `Embedding`
    - `Agent`, `AgentConfig`, `AgentSession`, `AgentInput`, `AgentOutputChunk`, `HumanFeedback`
    - `MemoryEntry`, `MemoryScope`, `MemoryQuery`; `Tool`, `ToolCall`, `ToolResult`, `PluginManifest`, `Plugin`
    - `Hook`, `HookEvent`, `HookContext`, `HookChainResult`
    - `Workflow`, `WorkflowRun`, `RunState`, `WorkflowDefinition`, `WorkflowNode`, `WorkflowEdge`
    - `CostRecord`, `EvalResult`, `PromptVersion`; `Tenant`, `User`, `ApiKey`
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 13.1, 14.1, 15.4_
  - [ ] 2.2 Implement full exception hierarchy from design section 16.1
    - `AetherOSError`, `DomainError`, `ValidationError`, `NotFoundError`, `ConflictError`
    - `InfrastructureError`, `AgentError`, `AgentRunAbortedError`, `AgentTimeoutError`
    - `WorkflowError`, `RoutingError`, `AuthError`, `PermissionDeniedError`, `RateLimitError`
    - `ToolError`, `ToolExecutionError`, `ToolDispatchError`, `HookAbortError`, `PluginError`
    - _Requirements: 18.5, 1.4, 7.8_
  - [ ]* 2.3 Write unit tests for domain entity invariants
    - Test frozen value objects cannot be mutated
    - Test AgentStatus and RunStatus enum membership
    - _Requirements: 23.1, 9.1_

- [ ] 3. Database migrations, schema, and repository interfaces
  - [ ] 3.1 Configure Alembic and write initial migration creating all tables from design section 15.3
    - `tenants`, `users`, `api_keys`, `agents`, `agent_sessions`, `workflows`, `workflow_runs`
    - `tools`, `plugins`, `hooks`, `cost_records`, `memory_entries` (with pgvector column)
    - Enable pgvector extension; create IVFFlat index on `memory_entries.embedding`
    - Enable Row-Level Security on all tenant-scoped tables
    - _Requirements: 15.1, 20.1, 20.8, 24.2_
  - [ ] 3.2 Implement SQLAlchemy ORM models mapping to all tables
    - Use `mapped_column` with proper types; JSONB columns use `JSON` type
    - All queries must use parameterized form — never raw string construction
    - _Requirements: 19.3, 15.1_
  - [ ] 3.3 Implement repository interfaces as Python Protocols
    - `AgentRepository`, `WorkflowRepository`, `MemoryRepository` matching design section 3.7
    - Add `SessionRepository`, `ToolRepository`, `PluginRepository`, `HookRepository`
    - Add `TenantRepository`, `UserRepository`, `ApiKeyRepository`, `CostRecordRepository`
    - _Requirements: 22.1, 22.2_
  - [ ] 3.4 Implement SQLAlchemy + asyncpg repository implementations for all protocols
    - Use `asyncpg` driver with pool min=5, max=20
    - Inject `tenant_id` via `SET app.current_tenant_id` before each query
    - _Requirements: 20.1, 15.1, 15.2_
  - [ ]* 3.5 Write integration tests for all repository implementations against test PostgreSQL
    - Test save/find/delete round-trips; test RLS isolation between tenants
    - _Requirements: 15.3_

- [ ] 4. Tenant, user, and authentication services
  - [ ] 4.1 Implement `TenantService` for creating tenants with tier assignment and resource quota application
    - Create tenant, assign tier (FREE/PRO/ENTERPRISE), apply rate limits and feature access
    - _Requirements: 15.4, 15.5, 17.5_
  - [ ] 4.2 Implement `AuthService` with JWT (RS256) and HMAC-SHA256 API key authentication
    - JWT validation via `python-jose`; API key hashing via `passlib[bcrypt]`
    - Store API keys only as bcrypt hashes; return raw key exactly once on creation
    - Reject expired API keys with HTTP 401
    - _Requirements: 16.1, 16.2, 16.3, 16.6, 16.7, 16.8_
  - [ ] 4.3 Implement RBAC authorization enforcement (admin/member/viewer/service roles)
    - `AuthService.authorize()` enforces role-based permissions per design section 13.3
    - _Requirements: 16.4, 16.5_
  - [ ]* 4.4 Write property test for API key authentication round-trip
    - **Property 17: API Key Authentication Round-Trip**
    - **Validates: Requirements 16.2, 16.6, 16.7**
  - [ ]* 4.5 Write unit tests for RBAC authorization rules
    - Test all three roles against create/read/update/delete actions
    - _Requirements: 16.4, 16.5_

- [ ] 5. FastAPI gateway — middleware stack and base API
  - [ ] 5.1 Implement FastAPI app factory with correlation ID, auth, rate-limit, and tenant middleware
    - Middleware order: auth → rate limit → routing (as required)
    - Attach `CorrelationId` to every request and propagate through all downstream calls
    - Structured JSON error handler mapping all `AetherOSError` subclasses to HTTP status codes
    - _Requirements: 18.1, 18.4, 18.5, 18.6, 12.5_
  - [ ] 5.2 Implement Redis token-bucket `RateLimiter` with per-tenant, per-type buckets
    - Separate buckets for API requests and LLM calls; replenish atomically via Redis Lua script
    - Enforce FREE/PRO/ENTERPRISE tier limits; return HTTP 429 on exhaustion
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_
  - [ ]* 5.3 Write unit tests for rate limiter token bucket logic
    - Test replenishment cap, exhaustion rejection, and per-type isolation
    - _Requirements: 17.6_
  - [ ] 5.4 Implement `FeatureFlagService` backed by Redis
    - Evaluate boolean feature flags at runtime without redeployment
    - _Requirements: 22.4_

- [ ] 6. Checkpoint — Phase 1 foundation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Memory subsystem — embedding, storage, and retrieval
  - [ ] 7.1 Implement `EmbeddingService` adapter wrapping OpenAI `text-embedding-3-small`
    - `embed(text)` and `embed_batch(texts)` async methods
    - Return `Embedding` with correct dimensions for the declared model
    - _Requirements: 3.3, 20.4_
  - [ ]* 7.2 Write property test for embedding dimensions invariant
    - **Property (derived from Req 4.3): EmbeddingService always returns Embedding.dimensions == model output size for non-empty input**
    - **Validates: Requirements 4.3**
  - [ ] 7.3 Implement `MemoryServiceImpl` — store, retrieve, delete, clear_scope, get_session_history
    - Vector search via pgvector cosine similarity with scope filter and oversampling
    - Apply entry_type and metadata filters post-vector-search
    - Re-rank with recency decay formula (RECENCY_WEIGHT=0.15, DECAY_RATE=0.01)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.14, 3.15, 3.16_
  - [ ]* 7.4 Write property test for memory retrieval score bounds
    - **Property 5: Memory Retrieval Score Bounds**
    - **Validates: Requirements 3.6**
  - [ ]* 7.5 Write property test for memory session history ordering
    - **Property 6: Memory Session History Ordering**
    - **Validates: Requirements 3.16**
  - [ ] 7.6 Implement `consolidate_long_term` with SUMMARIZE, EXTRACT_FACTS, and DEDUPLICATE strategies
    - Use `embed_batch()` for batched embedding during DEDUPLICATE
    - Delete all SESSION-scoped entries after consolidation; no-op when source is empty
    - _Requirements: 3.9, 3.10, 3.11, 3.12, 3.13, 20.4_
  - [ ]* 7.7 Write property test for memory persistence round-trip
    - **Property 7: Memory Persistence Round-Trip**
    - **Validates: Requirements 4.1, 4.4**
  - [ ]* 7.8 Write integration tests for MemoryService against test PostgreSQL + pgvector
    - Test vector search returns correct top-k entries; test scope isolation
    - _Requirements: 3.4, 3.7_

- [ ] 8. Tool & Plugin Registry
  - [ ] 8.1 Implement `ToolRegistryServiceImpl` — register, unregister, get, list, execute_tool
    - Dispatch to BUILTIN, MCP, PLUGIN, and CUSTOM handlers per design section 6.5
    - Validate arguments against parameter schema before dispatch
    - Emit PRE_TOOL_CALL and POST_TOOL_CALL HookEvents around execution
    - Record execution time in ToolResult
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14_
  - [ ]* 8.2 Write property test for tool argument validation
    - **Property 8: Tool Argument Validation**
    - **Validates: Requirements 5.5, 5.6**
  - [ ]* 8.3 Write property test for tool execution result invariant
    - **Property 9: Tool Execution Result Invariant**
    - **Validates: Requirements 5.12**
  - [ ] 8.4 Implement Plugin lifecycle — install, validate manifest, activate, deactivate, uninstall, upgrade
    - Validate manifest against `PLUGIN_MANIFEST_SCHEMA` (design section 8.2)
    - On activate: register all tools and hooks; on deactivate: unregister all tools and hooks
    - Enforce declared permissions at install and runtime
    - Roll back to previous active version if upgrade fails
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_
  - [ ]* 8.5 Write unit tests for plugin manifest validation and permission enforcement
    - Test valid and invalid manifests; test permission check blocks unlisted capabilities
    - _Requirements: 6.1, 6.9, 6.10_

- [ ] 9. Hook Engine
  - [ ] 9.1 Implement `HookEngineServiceImpl.emit_event` — priority-ordered chain execution
    - Load hooks from Redis cache (TTL=30s); filter by active, tenant, JSONLogic condition
    - Sort by priority ascending; blocking hooks awaited with timeout; non-blocking fire-and-forget
    - On timeout: log warning, record failed execution, continue chain
    - On `HookAbortError`: set `aborted=True`, return `HookChainResult` immediately
    - Record execution outcome (success/failure) in hook execution log
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12_
  - [ ]* 9.2 Write property test for hook chain priority order
    - **Property 10: Hook Chain Priority Order**
    - **Validates: Requirements 7.4**
  - [ ]* 9.3 Write property test for hook chain count bound
    - **Property 11: Hook Chain Count Bound**
    - **Validates: Requirements 7.9**
  - [ ]* 9.4 Write property test for hook abort propagation
    - **Property 12: Hook Abort Propagation**
    - **Validates: Requirements 7.8**
  - [ ] 9.5 Implement hook register, unregister, list, and get_hook_execution_log methods
    - Invalidate relevant Redis cache entries on unregister
    - Return execution history filtered by `hook_id` and `since` timestamp
    - _Requirements: 7.1, 7.13, 7.14_
  - [ ]* 9.6 Write unit tests for hook engine — timeout behavior and cache invalidation
    - Test timeout logs warning and continues; test unregister flushes cache
    - _Requirements: 7.7, 7.13_

- [ ] 10. Checkpoint — Phase 2 core services
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Agent Runtime Service
  - [ ] 11.1 Implement `AgentRuntimeServiceImpl.create_agent` with status IDLE and tenant association
    - Persist new Agent; associate with requesting TenantId
    - _Requirements: 1.1, 1.2_
  - [ ]* 11.2 Write property test for agent creation invariant
    - **Property 1: Agent Creation Invariant**
    - **Validates: Requirements 1.1, 1.2**
  - [ ] 11.3 Implement `start_agent` — session creation, PRE_AGENT_RUN hook, Langfuse trace start, LangGraph execution loop
    - Reject start if agent status is RUNNING or PAUSED (ConflictError)
    - Emit PRE_AGENT_RUN; abort if `hook_result.aborted=True`
    - Resolve system prompt from Langfuse by `system_prompt_id` or fall back to inline text; raise ValidationError if neither resolves
    - Build initial messages: SystemMessage → memory context → history → HumanMessage
    - Trim to `context_window_tokens` via token trimmer
    - Stream output chunks to Redis pub/sub channel
    - Handle timeout → `AgentTimeoutError`; handle max iterations; emit AGENT_ERROR on failure
    - Emit POST_AGENT_RUN; close Langfuse trace; persist session with `ended_at`
    - _Requirements: 1.3, 1.4, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.16, 2.1, 2.2, 2.3, 2.7, 2.8, 2.9, 2.10, 14.2, 14.3, 14.4_
  - [ ]* 11.4 Write property test for agent status state machine
    - **Property 2: Agent Status State Machine**
    - **Validates: Requirements 1.4, 23.1, 23.2, 23.3**
  - [ ]* 11.5 Write property test for iteration bound
    - **Property 3: Iteration Bound**
    - **Validates: Requirements 1.11, 2.5**
  - [ ]* 11.6 Write property test for initial message list structure
    - **Property 4: Initial Message List Structure**
    - **Validates: Requirements 2.1, 2.2**
  - [ ] 11.7 Implement `stop_agent`, `inject_human_feedback`, `list_agents`, and `stream_agent_output`
    - `stop_agent` → CANCELLED status, persist `ended_at`
    - `inject_human_feedback` → resume WAITING_FOR_HUMAN session via LangGraph resume
    - `list_agents` → paginated and filtered query scoped to tenant
    - `stream_agent_output` → AsyncIterator of AgentOutputChunk via Redis pub/sub
    - _Requirements: 1.5, 1.12, 1.13, 1.14, 1.15, 2.6_
  - [ ]* 11.8 Write unit tests for agent session state machine transitions
    - Test all valid transitions; test ConflictError on terminal re-transition; test ended_at invariant
    - _Requirements: 23.1, 23.2, 23.3, 23.4_

- [ ] 12. LangGraph Runtime — Graph Builder and Conditional Router
  - [ ] 12.1 Implement `LangGraphRuntime.build_graph` compiling `WorkflowDefinition` into `CompiledStateGraph`
    - Use `PostgresSaver` for checkpointing; cache compiled graph in Redis by `(workflow_id, version)`
    - Add all node types: AGENT, TOOL, CONDITION, HUMAN_INPUT, PARALLEL, WAIT, START, END
    - Wire conditional edges with sandboxed router (`__builtins__={}`)
    - _Requirements: 8.4, 8.5, 8.6, 8.17, 19.2_
  - [ ] 12.2 Implement `agent_node`, `human_input_node`, and `condition_router` node functions
    - `agent_node` calls `AgentRuntimeService.start_agent` and updates `AgentState`
    - `human_input_node` pauses via `interrupt()`; resumes with `HumanFeedback`
    - `condition_router` evaluates pre-compiled conditions; raises `RoutingError` if no match
    - _Requirements: 8.6, 8.7, 8.8, 8.9_
  - [ ]* 12.3 Write unit tests for conditional router with sample AgentState dicts
    - Test matching condition returns correct label; test no-match raises RoutingError
    - Test default edge fallback
    - _Requirements: 8.6, 8.7_

- [ ] 13. Workflow Service
  - [ ] 13.1 Implement `WorkflowService` — create, validate definition, run, get_run_state, list_runs
    - Validate: exactly one START node, one END node, all edge IDs reference defined nodes
    - Persist WorkflowRun in PENDING → compile graph → begin async execution
    - Checkpoint RunState to PostgreSQL at each node boundary
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.16_
  - [ ] 13.2 Implement pause_run, resume_run, cancel_run, and HUMAN_INPUT node handling
    - `pause_run` → PAUSED status; `resume_run` → restore checkpoint and continue
    - `cancel_run` → CANCELLED; HUMAN_INPUT node → WAITING_FOR_HUMAN + Redis publish (fire-and-forget)
    - Emit WORKFLOW_NODE_ENTER and WORKFLOW_NODE_EXIT HookEvents at every node
    - _Requirements: 8.9, 8.10, 8.11, 8.12, 8.15_
  - [ ]* 13.3 Write property test for workflow status state machine
    - **Property 13: Workflow Status State Machine**
    - **Validates: Requirements 9.1, 9.2**
  - [ ]* 13.4 Write property test for workflow completed-at invariant
    - **Property 14: Workflow Completed-At Invariant**
    - **Validates: Requirements 9.4**
  - [ ]* 13.5 Write unit tests for WorkflowService state transitions and RoutingError
    - Test PENDING→RUNNING→COMPLETED path; test terminal state rejection
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 14. Checkpoint — Phase 3 agent runtime and workflows
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. MCP Gateway — Client and Server
  - [ ] 15.1 Implement `MCPClientImpl` — connect, initialize, tools/list, tools/call, close
    - Support stdio, SSE, and WebSocket transports
    - On connect: register each MCPTool into `ToolRegistryService` as `ToolType.MCP`
    - On disconnect: unregister all tools registered from that session
    - Surface MCP error responses as `ToolResult(success=False)`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_
  - [ ] 15.2 Implement `AetherOSMCPServer` exposing agents/*, memory/*, workflows/*, and tools/* categories
    - Handle `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get`
    - Stop cleanly even if called while still starting; close all active connections on stop
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
  - [ ] 15.3 Implement `MCPGatewayService` wiring client and server into the application
    - `connect_mcp_client`, `disconnect_mcp_client`, `call_mcp_tool`, `list_mcp_tools`
    - `start_mcp_server`, `stop_mcp_server`
    - _Requirements: 10.1, 10.6, 11.4_
  - [ ]* 15.4 Write integration tests for MCP client/server round-trip
    - Test tool call proxy: client → external MCP server → ToolResult
    - Test disconnect unregisters tools
    - _Requirements: 10.2, 10.4_

- [ ] 16. Observability — Langfuse, OpenTelemetry, Prometheus, and cost tracking
  - [ ] 16.1 Implement `LangfuseTracingService` — start_trace, log_generation, log_span, end_trace, submit_eval
    - Record trace_id on AgentSession; record Langfuse Generation for each LLM call
    - Record Langfuse Span nested under trace for each tool call
    - Close trace on session end with final output and errors
    - Support `PromptVersion` create and resolve via Langfuse
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 14.1_
  - [ ] 16.2 Implement `CostTrackingService` — record_llm_cost, get_cost_summary, check_budget_limit
    - Create `CostRecord` on every LLM call completion; enforce non-negative cost_usd and total_tokens
    - Aggregate by tenant + time window; enforce FREE tier monthly token budget
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  - [ ]* 16.3 Write property test for cost record non-negativity
    - **Property 15: Cost Record Non-Negativity**
    - **Validates: Requirements 13.2**
  - [ ] 16.4 Implement OpenTelemetry instrumentation and Prometheus metrics emission
    - Auto-instrument FastAPI via `opentelemetry-instrumentation-fastapi`
    - Emit all 10 Prometheus metrics defined in design section 12.2
    - Ship logs to Loki via Promtail configuration
    - _Requirements: 12.5, 12.6, 12.8_
  - [ ]* 16.5 Write unit tests for cost tracking aggregation and budget enforcement
    - Test correct grouping by model; test FREE tier budget limit rejects over-limit tenants
    - _Requirements: 13.3, 13.4, 13.5_

- [ ] 17. Security controls — audit log, prompt injection guard, and TLS config
  - [ ] 17.1 Implement immutable audit log for all create/update/delete operations
    - Audit entries cannot be modified or deleted by application code
    - _Requirements: 19.5_
  - [ ] 17.2 Implement `PromptInjectionGuard` hook handler registered on PRE_LLM_CALL
    - Inspects prompt payload before it reaches the LLM provider
    - _Requirements: 19.1_
  - [ ] 17.3 Enforce parameterized queries throughout all database access code
    - Audit all repository implementations; replace any raw SQL string construction
    - _Requirements: 19.3_
  - [ ]* 17.4 Write unit tests for audit log immutability and prompt injection guard
    - Test audit entries cannot be altered post-write; test guard hooks fire on PRE_LLM_CALL
    - _Requirements: 19.1, 19.5_

- [ ] 18. Checkpoint — Phase 4-6 observability and security
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Tenant isolation property test and multi-tenancy hardening
  - [ ] 19.1 Implement application-level tenant_id ownership validation in all service layer queries
    - Every entity access must validate the authenticated tenant_id matches the entity's tenant_id
    - _Requirements: 15.2, 15.3_
  - [ ]* 19.2 Write property test for tenant data isolation
    - **Property 16: Tenant Data Isolation**
    - **Validates: Requirements 15.3**
  - [ ]* 19.3 Write integration tests verifying RLS prevents cross-tenant data access
    - Create entities for T1 and T2; assert T1 queries return zero T2 entities
    - _Requirements: 15.1, 15.3_

- [ ] 20. REST API routers for all bounded contexts
  - [ ] 20.1 Implement FastAPI routers for Agent Runtime — agents CRUD, session start/stop, human feedback
    - Endpoints under `/api/v1/agents/` and `/api/v1/sessions/`
    - WebSocket endpoint `/api/v1/sessions/{id}/stream` with same auth as REST
    - _Requirements: 18.1, 18.2, 18.3_
  - [ ] 20.2 Implement FastAPI routers for Workflows, Memory, Tools, Plugins, and Hooks
    - Endpoints under `/api/v1/workflows/`, `/api/v1/memory/`, `/api/v1/tools/`, `/api/v1/plugins/`, `/api/v1/hooks/`
    - _Requirements: 18.1_
  - [ ] 20.3 Implement FastAPI routers for Observability, Auth/Tenants, and MCP Gateway
    - Endpoints under `/api/v1/observability/`, `/api/v1/auth/`, `/api/v1/tenants/`, `/api/v1/mcp/`
    - _Requirements: 18.1_
  - [ ] 20.4 Implement Pydantic request/response schemas for all routers
    - Input schemas validate incoming payloads; output schemas serialize domain entities
    - _Requirements: 18.5_
  - [ ]* 20.5 Write integration tests for critical REST endpoints
    - Test agent run flow end-to-end; test 401/403/422/429 error responses
    - _Requirements: 18.5, 16.3, 16.5_

- [ ] 21. React/Vite frontend dashboard
  - [ ] 21.1 Initialize Vite + React + TailwindCSS project under `frontend/` with all declared packages
    - Configure `@tanstack/react-query`, `zustand`, `axios`, `reactflow`, `recharts`, `@radix-ui`
    - Set up Zustand `authStore` and `tenantStore`; Axios instance with JWT interceptor
    - _Requirements: 21.1, 21.4, 21.5, 21.7_
  - [ ] 21.2 Implement `useAgentStream` WebSocket hook and `StreamingOutput` component
    - Connect to `/api/v1/sessions/{id}/stream`; render AgentOutputChunks progressively
    - Show "reconnecting" indicator on disconnect; resume on reconnect; show "disconnected" after exhausted retries
    - _Requirements: 21.2, 21.6_
  - [ ] 21.3 Implement Agent Management views — AgentList, AgentDetail, AgentRunPanel, AgentConfigForm
    - Use TanStack Query for data fetching with cache invalidation
    - _Requirements: 21.1, 21.4_
  - [ ] 21.4 Implement Workflow Editor with React Flow visual node editor and WorkflowRunDetail view
    - Interactive node editor for creating and editing workflow graphs
    - _Requirements: 21.3_
  - [ ] 21.5 Implement remaining dashboard views — MemoryExplorer, ToolRegistry, PluginManager, Observability views, Settings
    - TraceViewer, CostDashboard, EvalDashboard, TenantSettings, UserManagement, ApiKeys
    - _Requirements: 21.1_
  - [ ]* 21.6 Write unit tests for useAgentStream hook reconnection logic
    - Test reconnecting state; test disconnected state after max retries; test indicator hide on reconnect
    - _Requirements: 21.6_

- [ ] 22. Infrastructure — Docker Compose, CI pipeline, and Kubernetes manifests
  - [ ] 22.1 Write `docker-compose.yml` defining all 11 services from design section 15.1
    - Services: api, worker, frontend, postgres, redis, langfuse, otel, prometheus, grafana, loki, promtail
    - API startup must run Alembic migrations and refuse to start if migrations fail
    - _Requirements: 24.1, 24.2_
  - [ ] 22.2 Implement CI pipeline `.github/workflows/ci.yml`
    - Jobs: ruff + black + mypy lint; pytest unit + integration with coverage; E2E via docker compose; docker build; Trivy scan
    - _Requirements: 24.3_
  - [ ] 22.3 Write Kubernetes manifests and Helm chart for production deployment
    - Deployments for api and worker; Services; ConfigMaps; Secrets referencing env vars
    - Secret management via Kubernetes Secrets or AWS Secrets Manager
    - _Requirements: 24.4, 24.5_
  - [ ]* 22.4 Write E2E tests covering full agent run, workflow with conditional edges, human-in-the-loop, and plugin installation
    - Run against docker-compose stack
    - _Requirements: 1.3, 8.10, 6.4_

- [ ] 23. Final checkpoint — wire everything together and verify
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP delivery
- Each task references specific requirements from `requirements.md` for traceability
- Property tests use the `hypothesis` library as declared in the design's testing strategy
- The seven-phase roadmap is embedded in the task ordering: tasks 1–6 = Phase 1, tasks 7–10 = Phase 2, tasks 11–14 = Phase 3, tasks 15–18 = Phases 4–6, tasks 19–23 = Phase 7
- All code must pass `ruff`, `black`, and `mypy` checks before merging
- Checkpoints validate incremental correctness; never skip a checkpoint task

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "2.1", "2.2"] },
    { "id": 2, "tasks": ["1.4", "2.3", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3"] },
    { "id": 4, "tasks": ["3.4", "4.1", "4.2"] },
    { "id": 5, "tasks": ["3.5", "4.3", "5.1"] },
    { "id": 6, "tasks": ["4.4", "4.5", "5.2", "5.4"] },
    { "id": 7, "tasks": ["5.3", "7.1", "8.1"] },
    { "id": 8, "tasks": ["7.2", "7.3", "8.4", "9.1"] },
    { "id": 9, "tasks": ["7.4", "7.5", "7.6", "8.2", "8.3", "9.2", "9.3", "9.4", "9.5"] },
    { "id": 10, "tasks": ["7.7", "7.8", "8.5", "9.6", "11.1", "12.1"] },
    { "id": 11, "tasks": ["11.2", "11.3", "12.2", "13.1"] },
    { "id": 12, "tasks": ["11.4", "11.5", "11.6", "11.7", "12.3", "13.2"] },
    { "id": 13, "tasks": ["11.8", "13.3", "13.4", "15.1"] },
    { "id": 14, "tasks": ["13.5", "15.2", "16.1"] },
    { "id": 15, "tasks": ["15.3", "16.2", "16.4", "17.1", "17.2", "17.3"] },
    { "id": 16, "tasks": ["15.4", "16.3", "16.5", "17.4", "19.1"] },
    { "id": 17, "tasks": ["19.2", "19.3", "20.1"] },
    { "id": 18, "tasks": ["20.2", "20.3"] },
    { "id": 19, "tasks": ["20.4", "21.1"] },
    { "id": 20, "tasks": ["20.5", "21.2"] },
    { "id": 21, "tasks": ["21.3", "21.4"] },
    { "id": 22, "tasks": ["21.5", "22.1"] },
    { "id": 23, "tasks": ["21.6", "22.2"] },
    { "id": 24, "tasks": ["22.3", "22.4"] }
  ]
}
```
