# Implementation Tasks: AetherOS — AI Agent Runtime Platform

> **Format legend**
> `[BE]` Backend · `[FE]` Frontend · `[INF]` Infrastructure · `[DOC]` Documentation
> `Deps:` task IDs that must be complete first
> `Files:` files to create (`+`) or modify (`~`)
> `Validates:` requirement clause(s)

---

## Phase 1 — Foundation

---

### Task 1.1 — Initialize Python project layout `[BE]`
**Estimate:** 1 h
**Deps:** none
**Files:**
- `+` `backend/pyproject.toml`
- `+` `backend/src/aetheros/__init__.py`
- `+` `backend/src/aetheros/api/__init__.py`
- `+` `backend/src/aetheros/application/__init__.py`
- `+` `backend/src/aetheros/domain/__init__.py`
- `+` `backend/src/aetheros/infrastructure/__init__.py`
- `+` `backend/src/aetheros/config/__init__.py`
- `+` `backend/src/aetheros/main.py`
- `+` `backend/src/aetheros/container.py`

**Validation criteria:**
- `pyproject.toml` declares Python `>=3.13`, all runtime deps with pinned minor versions
- `ruff`, `black`, `mypy` configs present in `pyproject.toml`
- `python -c "import aetheros"` succeeds

**Testing requirements:**
- No tests at this stage; confirm `pytest --collect-only` runs without import errors

**Validates:** Req 22.1, 24.3


---

### Task 1.2 — Implement `Settings` and environment loading `[BE]`
**Estimate:** 1 h
**Deps:** 1.1
**Files:**
- `+` `backend/src/aetheros/config/settings.py`
- `+` `backend/.env.example`

**Validation criteria:**
- `Settings()` raises `ValidationError` when any required field is absent
- All fields: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ENVIRONMENT`
- Loading from `.env` file and environment variables both work

**Testing requirements:**
- Unit test: instantiating `Settings` without env vars raises `pydantic.ValidationError`
- Unit test: all required fields load correctly from a mocked env dict

**Validates:** Req 22.3, 19.4

---

### Task 1.3 — Implement DI `Container` class `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.2
**Files:**
- `~` `backend/src/aetheros/container.py`

**Validation criteria:**
- Container wires: `Settings`, DB engine, Redis pool, all repository impls, all service impls
- Calling `Container()` with missing config raises before any service is accessible
- No infrastructure adapter instantiated outside the container

**Testing requirements:**
- Unit test: `Container` with incomplete `Settings` raises `RuntimeError` or `ValidationError` before completing init
- Property test (hypothesis): for any randomly-omitted required config field, init always raises

**Validates:** Req 22.1, 22.2, 22.3

---

### Task 1.4 — Implement value objects and enums `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.1
**Files:**
- `+` `backend/src/aetheros/domain/shared/value_objects.py`
- `+` `backend/src/aetheros/domain/agents/enums.py`
- `+` `backend/src/aetheros/domain/workflows/enums.py`
- `+` `backend/src/aetheros/domain/memory/enums.py`
- `+` `backend/src/aetheros/domain/tools/enums.py`
- `+` `backend/src/aetheros/domain/hooks/enums.py`

**Validation criteria:**
- `AgentId`, `TenantId`, `SessionId`, `WorkflowId`, `RunId`, `MemoryEntryId`, `ToolId`, `PluginId`, `HookId` are frozen dataclasses
- `Embedding(vector, model, dimensions)` is frozen
- All status enums: `AgentStatus`, `RunStatus`, `MemoryScopeType`, `MemoryEntryType`, `ToolType`, `HookEventType`, `HookPriority`, `TenantTier`, `ConsolidationStrategy`
- `mypy` reports no errors on these files

**Testing requirements:**
- Unit test: frozen value objects raise `FrozenInstanceError` on mutation attempt
- Unit test: all enum members match design section 4 exactly

**Validates:** Req 1.1, 2.1, 3.1, 5.1, 7.1, 8.1


---

### Task 1.5 — Implement domain entity dataclasses `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.4
**Files:**
- `+` `backend/src/aetheros/domain/agents/entities.py`
- `+` `backend/src/aetheros/domain/memory/entities.py`
- `+` `backend/src/aetheros/domain/tools/entities.py`
- `+` `backend/src/aetheros/domain/hooks/entities.py`
- `+` `backend/src/aetheros/domain/workflows/entities.py`
- `+` `backend/src/aetheros/domain/observability/entities.py`
- `+` `backend/src/aetheros/domain/tenants/entities.py`

**Validation criteria:**
- All entities match design section 4 exactly: `Agent`, `AgentConfig`, `AgentSession`, `AgentInput`, `AgentOutputChunk`, `HumanFeedback`, `MemoryEntry`, `MemoryScope`, `MemoryQuery`, `Tool`, `ToolCall`, `ToolResult`, `PluginManifest`, `Plugin`, `Hook`, `HookDefinition`, `HookEvent`, `HookContext`, `HookChainResult`, `Workflow`, `WorkflowRun`, `RunState`, `WorkflowDefinition`, `WorkflowNode`, `WorkflowEdge`, `CostRecord`, `EvalResult`, `PromptVersion`, `Tenant`, `User`, `ApiKey`
- `mypy --strict` passes on all entity files

**Testing requirements:**
- Unit test: each entity can be instantiated with valid data
- Unit test: `AgentSession.ended_at` is `None` by default

**Validates:** Req 1.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 13.1, 15.4

---

### Task 1.6 — Implement exception hierarchy `[BE]`
**Estimate:** 45 min
**Deps:** 1.1
**Files:**
- `+` `backend/src/aetheros/domain/shared/exceptions.py`

**Validation criteria:**
- Full hierarchy as per design section 16.1: `AetherOSError`, `DomainError`, `ValidationError`, `NotFoundError`, `ConflictError`, `InfrastructureError`, `DatabaseError`, `CacheError`, `LLMProviderError`, `MCPError`, `AgentError`, `AgentRunAbortedError`, `AgentTimeoutError`, `MaxIterationsError`, `WorkflowError`, `RoutingError`, `AuthError`, `PermissionDeniedError`, `RateLimitError`, `ToolError`, `ToolExecutionError`, `ToolDispatchError`, `HookAbortError`, `PluginError`
- Each exception stores `message`, `error_code`, optional `details`

**Testing requirements:**
- Unit test: each exception is a subclass of the correct parent
- Unit test: HTTP error mapping table (design 16.2) can be derived from exception types

**Validates:** Req 18.5, 1.4, 7.8

---

### Task 1.7 — Implement repository Protocol interfaces `[BE]`
**Estimate:** 1 h
**Deps:** 1.5
**Files:**
- `+` `backend/src/aetheros/domain/agents/repositories.py`
- `+` `backend/src/aetheros/domain/workflows/repositories.py`
- `+` `backend/src/aetheros/domain/memory/repositories.py`
- `+` `backend/src/aetheros/domain/tools/repositories.py`
- `+` `backend/src/aetheros/domain/hooks/repositories.py`
- `+` `backend/src/aetheros/domain/tenants/repositories.py`
- `+` `backend/src/aetheros/domain/observability/repositories.py`

**Validation criteria:**
- All repository Protocols match design section 3.7 signatures
- Includes: `AgentRepository`, `SessionRepository`, `WorkflowRepository`, `MemoryRepository`, `ToolRepository`, `PluginRepository`, `HookRepository`, `TenantRepository`, `UserRepository`, `ApiKeyRepository`, `CostRecordRepository`
- `mypy` validates all `Protocol` definitions with no errors

**Testing requirements:**
- No runtime tests; `mypy` type-checking serves as validation

**Validates:** Req 22.1, 22.2


---

### Task 1.8 — Configure Alembic and write initial DB migration `[BE]` `[INF]`
**Estimate:** 1.5 h
**Deps:** 1.1
**Files:**
- `+` `backend/alembic.ini`
- `+` `backend/alembic/env.py`
- `+` `backend/alembic/versions/0001_initial_schema.py`

**Validation criteria:**
- Migration creates all tables: `tenants`, `users`, `api_keys`, `agents`, `agent_sessions`, `workflows`, `workflow_runs`, `tools`, `plugins`, `hooks`, `cost_records`, `memory_entries`
- `memory_entries.embedding` is `VECTOR(1536)` column
- IVFFlat index created on `memory_entries.embedding` with `lists=100`
- RLS enabled on all tenant-scoped tables with policy `tenant_id = current_setting('app.current_tenant_id')::uuid`
- `alembic upgrade head` completes without errors against a fresh PostgreSQL instance

**Testing requirements:**
- Integration test: run migration on test DB, assert all tables and indexes exist via `pg_catalog` queries
- Integration test: downgrade migration runs cleanly

**Validates:** Req 15.1, 20.1, 20.8, 24.2

---

### Task 1.9 — Implement SQLAlchemy ORM models `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.7, 1.8
**Files:**
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/models.py`

**Validation criteria:**
- ORM models map 1:1 to all tables from Task 1.8
- `mapped_column` used with explicit types; JSONB columns use `JSON` type
- All FK relationships declared
- No raw SQL string construction anywhere in the file
- `mypy` passes

**Testing requirements:**
- Unit test: each ORM model can be instantiated and serialized to dict
- Integration test: `session.add(model_instance)` then `session.commit()` round-trips correctly

**Validates:** Req 19.3, 15.1

---

### Task 1.10 — Implement async repository implementations `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.9
**Files:**
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/agent_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/workflow_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/memory_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/tool_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/hook_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/tenant_repository.py`
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/cost_record_repository.py`

**Validation criteria:**
- All use `asyncpg` driver via SQLAlchemy async session
- Connection pool configured: `pool_min_size=5`, `pool_max_size=20`
- Every query method calls `SET app.current_tenant_id = :tid` before executing
- No raw SQL string construction; all queries use ORM or `text()` with bound params
- Each implementation class satisfies its Protocol at `mypy` level

**Testing requirements:**
- Integration test per repo: save → find_by_id round-trip
- Integration test: `find_by_tenant` returns only entities for that tenant
- Integration test: delete removes entity; subsequent find returns `None`

**Validates:** Req 20.1, 15.1, 15.2


---

### Task 1.11 — Implement `TenantService` `[BE]`
**Estimate:** 1 h
**Deps:** 1.10
**Files:**
- `+` `backend/src/aetheros/application/tenants/tenant_service.py`

**Validation criteria:**
- `create_tenant(name, tier)` persists a `Tenant` with correct tier and returns it
- Tier assignment applies correct rate-limit and feature-access config from `Settings`
- `get_tenant(tenant_id)` raises `NotFoundError` if absent

**Testing requirements:**
- Unit test (mocked repo): creating a tenant with each tier produces correct settings
- Unit test: `get_tenant` with unknown ID raises `NotFoundError`

**Validates:** Req 15.4, 15.5, 17.5

---

### Task 1.12 — Implement `AuthService` — JWT authentication `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.10
**Files:**
- `+` `backend/src/aetheros/application/tenants/auth_service.py`

**Validation criteria:**
- `authenticate_jwt(token)` validates RS256 signature using `python-jose`
- Returns populated `AuthContext(tenant_id, user_id, scopes, is_service_account)`
- Raises `AuthError` (HTTP 401) for invalid/expired tokens

**Testing requirements:**
- Unit test: valid JWT returns correct `AuthContext`
- Unit test: expired JWT raises `AuthError`
- Unit test: JWT with wrong algorithm raises `AuthError`

**Validates:** Req 16.1, 16.3

---

### Task 1.13 — Implement `AuthService` — API key authentication `[BE]`
**Estimate:** 1 h
**Deps:** 1.12
**Files:**
- `~` `backend/src/aetheros/application/tenants/auth_service.py`

**Validation criteria:**
- `authenticate_api_key(raw_key)` hashes with HMAC-SHA256, compares to bcrypt hash in DB
- `create_api_key()` returns raw key exactly once; stores only bcrypt hash
- Expired keys rejected with HTTP 401
- Raw key never written to DB, logs, or traces

**Testing requirements:**
- Unit test: API key round-trip — create key, authenticate with raw value, get correct `AuthContext`
- Unit test: expired key raises `AuthError`
- Unit test: tampered key raises `AuthError`
- Property test (hypothesis): for any random key string, stored hash never equals the raw input

**Validates:** Req 16.2, 16.6, 16.7, 16.8

---

### Task 1.14 — Implement RBAC `authorize()` `[BE]`
**Estimate:** 1 h
**Deps:** 1.12
**Files:**
- `~` `backend/src/aetheros/application/tenants/auth_service.py`

**Validation criteria:**
- `authorize(context, resource, action)` enforces table in design 13.3
- `admin`: full CRUD on all tenant resources
- `member`: create/run agents and workflows, read all resources
- `viewer`: read-only
- Raises `PermissionDeniedError` (HTTP 403) on denied action

**Testing requirements:**
- Unit tests: all three roles × CRUD actions — assert allowed/denied per matrix
- Unit test: `PermissionDeniedError` raised for viewer attempting a write

**Validates:** Req 16.4, 16.5


---

### Task 1.15 — Implement Redis token-bucket `RateLimiter` `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.2
**Files:**
- `+` `backend/src/aetheros/infrastructure/persistence/redis/rate_limiter.py`
- `+` `backend/src/aetheros/infrastructure/persistence/redis/scripts/token_bucket.lua`

**Validation criteria:**
- Separate buckets for `api_requests` and `llm_calls` per tenant
- Replenishment uses atomic Lua script; bucket never exceeds configured max
- Enforces FREE / PRO / ENTERPRISE limits from `Settings`
- Returns `(allowed: bool, remaining: int, retry_after_ms: int)`

**Testing requirements:**
- Unit test (mock Redis): decrement allows until bucket = 0, then rejects
- Unit test: replenishment caps at max capacity
- Unit test: per-type isolation — exhausting `llm_calls` bucket does not affect `api_requests` bucket
- Integration test: concurrent requests respect atomicity via Redis

**Validates:** Req 17.1, 17.2, 17.3, 17.4, 17.5, 17.6

---

### Task 1.16 — Implement `FeatureFlagService` `[BE]`
**Estimate:** 45 min
**Deps:** 1.2
**Files:**
- `+` `backend/src/aetheros/infrastructure/persistence/redis/feature_flag_service.py`

**Validation criteria:**
- `is_enabled(flag_name, tenant_id)` reads from Redis hash; returns `bool`
- `set_flag(flag_name, tenant_id, value)` writes to Redis
- Returns `False` (safe default) when flag key does not exist

**Testing requirements:**
- Unit test (mock Redis): flag set to `True` returns `True`; missing flag returns `False`
- Unit test: flag can be toggled without service restart

**Validates:** Req 22.4

---

### Task 1.17 — Implement FastAPI app factory and middleware stack `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.13, 1.14, 1.15
**Files:**
- `~` `backend/src/aetheros/main.py`
- `+` `backend/src/aetheros/api/middleware/correlation.py`
- `+` `backend/src/aetheros/api/middleware/auth.py`
- `+` `backend/src/aetheros/api/middleware/rate_limit.py`
- `+` `backend/src/aetheros/api/middleware/tenant.py`
- `+` `backend/src/aetheros/api/v1/health.py`

**Validation criteria:**
- Middleware order enforced: auth → rate limit → routing
- `CorrelationId` UUID generated and attached to every request; propagated to all downstream calls via `contextvars`
- Unhandled `AetherOSError` subclasses map to correct HTTP status codes (design 16.2)
- `GET /api/v1/health` returns `{"status": "ok"}` with HTTP 200

**Testing requirements:**
- Integration test: unauthenticated request returns HTTP 401 before rate limit check
- Integration test: rate-limited request returns HTTP 429 with `RATE_LIMIT_EXCEEDED`
- Integration test: every response includes `X-Correlation-ID` header
- Integration test: unknown `AetherOSError` returns HTTP 500

**Validates:** Req 18.1, 18.4, 18.5, 18.6, 12.5


---

## Phase 2 — Memory & Tools

---

### Task 2.1 — Implement `EmbeddingService` adapter `[BE]`
**Estimate:** 1 h
**Deps:** 1.5
**Files:**
- `+` `backend/src/aetheros/infrastructure/embedding/openai_embedding_service.py`

**Validation criteria:**
- `embed(text: str) -> Embedding` calls OpenAI `text-embedding-3-small` asynchronously
- `embed_batch(texts: list[str]) -> list[Embedding]` batches in a single API call
- Returns `Embedding(vector, model, dimensions=1536)`
- Raises `LLMProviderError` on API failure with original error wrapped

**Testing requirements:**
- Unit test (mock OpenAI client): `embed("hello")` returns `Embedding` with `dimensions=1536`
- Unit test: `embed_batch(["a", "b"])` returns two `Embedding` objects
- Property test (hypothesis): for any non-empty string, returned `Embedding.dimensions` equals 1536

**Validates:** Req 3.3, 4.3, 20.4

---

### Task 2.2 — Implement `MemoryRepository` vector search `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.10
**Files:**
- `~` `backend/src/aetheros/infrastructure/persistence/postgres/memory_repository.py`

**Validation criteria:**
- `vector_search(embedding, scope, top_k)` issues pgvector cosine similarity query: `ORDER BY embedding <=> $1 LIMIT $2`
- Scope filter applied at SQL level: `WHERE scope_type = $3 AND scope_id = $4`
- Returns `list[MemoryEntry]` with `relevance_score` populated from cosine distance
- Uses parameterized query exclusively — no string interpolation

**Testing requirements:**
- Integration test: store 5 entries, query with embedding closest to entry #3, assert entry #3 is rank 1
- Integration test: scope filter ensures entries from other scopes are not returned

**Validates:** Req 3.4, 15.3, 19.3

---

### Task 2.3 — Implement `MemoryServiceImpl` — store/retrieve/delete `[BE]`
**Estimate:** 1.5 h
**Deps:** 2.1, 2.2
**Files:**
- `+` `backend/src/aetheros/application/memory/memory_service.py`

**Validation criteria:**
- `store(entry, scope)` computes embedding if absent, persists to `memory_entries`
- `retrieve(query, scope, top_k)` embeds query if no pre-computed embedding; fetches `top_k × 3` candidates; applies `entry_types` and `metadata` filters; re-ranks with recency decay formula: `score = 0.85 × similarity + 0.15 × exp(-0.01 × age_hours)`; clips scores to `[0.0, 1.0]`
- `delete(entry_id)` removes entry
- `clear_scope(scope)` deletes all entries for that scope
- `get_session_history(session_id)` returns entries ordered by `created_at ASC`

**Testing requirements:**
- Unit test (mock repo): `retrieve` calls `embed` only when `query.embedding` is `None`
- Unit test: recency decay formula produces scores in `[0.0, 1.0]` for any age ≥ 0
- Property test: all `relevance_score` values in returned list are within `[0.0, 1.0]`
- Property test: `get_session_history` result is strictly ordered by `created_at`

**Validates:** Req 3.1–3.8, 3.14–3.16

---

### Task 2.4 — Implement `consolidate_long_term` — all three strategies `[BE]`
**Estimate:** 1.5 h
**Deps:** 2.3
**Files:**
- `~` `backend/src/aetheros/application/memory/memory_service.py`

**Validation criteria:**
- `SUMMARIZE`: calls LLM to produce narrative summary; persists as `SUMMARY`-type `MemoryEntry` in `AGENT` scope
- `EXTRACT_FACTS`: calls LLM to extract facts; persists each as `FACT`-type entry in `AGENT` scope
- `DEDUPLICATE`: calls `embed_batch()` on all session entries; clusters by cosine similarity; persists centroid of each cluster in `AGENT` scope
- All strategies: deletes all `SESSION`-scoped entries for `agent_id` after consolidation
- No-op (no new entries, no deletes) when source entries list is empty

**Testing requirements:**
- Unit test (mock LLM): `SUMMARIZE` produces exactly one new `SUMMARY` entry
- Unit test: empty session entries — no new entries created, no deletes issued
- Unit test: `DEDUPLICATE` calls `embed_batch` not individual `embed` per entry

**Validates:** Req 3.9–3.13, 20.4


---

### Task 2.5 — Implement `ToolRegistryServiceImpl` — register/unregister/list `[BE]`
**Estimate:** 1 h
**Deps:** 1.10
**Files:**
- `+` `backend/src/aetheros/application/tools/tool_registry_service.py`

**Validation criteria:**
- `register_tool(definition)` persists `Tool` with correct `ToolId`, schema, `handler_ref`, and `tenant_id`
- `register_tool` with `tenant_id=None` makes tool platform-wide (visible to all tenants)
- `unregister_tool(tool_id)` removes entry; subsequent `get_tool` raises `NotFoundError`
- `list_tools(filters)` returns only tools matching all filter criteria accessible to requesting tenant

**Testing requirements:**
- Unit test (mock repo): registered tool is returned by `list_tools` for owning tenant
- Unit test: platform-wide tool appears in `list_tools` for any tenant
- Unit test: unregistered tool raises `NotFoundError` on `get_tool`

**Validates:** Req 5.1, 5.2, 5.3, 5.4

---

### Task 2.6 — Implement `ToolRegistryServiceImpl` — `execute_tool` dispatcher `[BE]`
**Estimate:** 1.5 h
**Deps:** 2.5
**Files:**
- `~` `backend/src/aetheros/application/tools/tool_registry_service.py`
- `+` `backend/src/aetheros/application/tools/builtin_handler_registry.py`

**Validation criteria:**
- `execute_tool(call, context)` validates `call.arguments` against tool's parameter schema before dispatch; raises `ValidationError` on mismatch (never invokes handler)
- Raises `NotFoundError` if `tool_id` absent or not enabled for tenant
- Dispatches `BUILTIN` → `builtin_handler_registry[tool_id].execute(args, ctx)`
- Dispatches `PLUGIN` → `plugin_loader.invoke(plugin_id, tool_id, args, ctx)`
- Dispatches `CUSTOM` → dynamic import of `handler_ref`, then `await handler(args, ctx)`
- `ToolResult.success=True` + `execution_time_ms` recorded on success
- `ToolResult.success=False` + error message on `ToolExecutionError`
- Emits `PRE_TOOL_CALL` hook before dispatch and `POST_TOOL_CALL` hook after result

**Testing requirements:**
- Unit test: invalid args → `ValidationError` raised; handler not called
- Unit test: unknown tool_id → `NotFoundError`
- Unit test: `BUILTIN` dispatch invokes handler and returns success result
- Unit test: handler raises `ToolExecutionError` → `ToolResult.success=False`
- Property test: successful execution always produces `ToolResult` with `execution_time_ms >= 0`

**Validates:** Req 5.5–5.14

---

### Task 2.7 — Implement Plugin install/activate/deactivate/uninstall `[BE]`
**Estimate:** 1.5 h
**Deps:** 2.6
**Files:**
- `+` `backend/src/aetheros/application/tools/plugin_service.py`
- `+` `backend/src/aetheros/domain/tools/plugin_manifest_schema.py`

**Validation criteria:**
- `install_plugin(manifest, tenant_id)` validates manifest against `PLUGIN_MANIFEST_SCHEMA` (design 8.2); rejects with `ValidationError` listing violations
- Persists plugin in `Inactive` state on successful validation
- `enable_plugin(plugin_id)` transitions to `Active`; registers all declared tools and hooks
- `disable_plugin(plugin_id)` transitions to `Inactive`; unregisters all tools and hooks
- `uninstall_plugin(plugin_id)` removes plugin and all its tools/hooks
- `upgrade_plugin(plugin_id, new_manifest)` rolls back to previous active version if upgrade fails
- All permission strings validated against allowed set: `memory:read`, `memory:write`, `tools:execute`, `agents:read`, `http:outbound`

**Testing requirements:**
- Unit test: manifest missing required `tools` field raises `ValidationError`
- Unit test: manifest with invalid permission string raises `ValidationError`
- Unit test: enable plugin registers all declared tools
- Unit test: disable plugin unregisters all declared tools
- Unit test: failed upgrade leaves previous version active

**Validates:** Req 6.1–6.10


---

## Phase 3 — Hook Engine

---

### Task 3.1 — Implement `HookEngineServiceImpl` — register/unregister/cache `[BE]`
**Estimate:** 1 h
**Deps:** 1.10, 1.16
**Files:**
- `+` `backend/src/aetheros/application/hooks/hook_engine_service.py`

**Validation criteria:**
- `register_hook(definition)` persists `Hook` with all fields; returns `Hook`
- `unregister_hook(hook_id)` removes hook from DB and invalidates Redis cache for that `event_type`
- `list_hooks(event_type)` returns all active hooks for that event type
- `get_hook_execution_log(hook_id, since)` returns `HookExecution` records filtered by `hook_id` and `since`
- Cache key pattern: `hooks:{event_type}:{tenant_id}`, TTL = 30 s default

**Testing requirements:**
- Unit test: registered hook appears in `list_hooks`
- Unit test: `unregister_hook` flushes the matching Redis cache key
- Unit test: `get_hook_execution_log` returns records after `since` timestamp only

**Validates:** Req 7.1, 7.13, 7.14

---

### Task 3.2 — Implement `HookEngineServiceImpl.emit_event` — chain execution `[BE]`
**Estimate:** 1.5 h
**Deps:** 3.1
**Files:**
- `~` `backend/src/aetheros/application/hooks/hook_engine_service.py`

**Validation criteria:**
- Loads hooks from Redis cache (falls back to DB on cache miss); filters by `is_active`, `tenant_id` match (or platform-wide), and JSONLogic condition evaluated against event payload
- Sorts by `HookPriority.value` ascending (lower = first)
- Blocking hooks: `await asyncio.wait_for(handler, timeout=hook.timeout_ms / 1000)` then merges returned payload
- Non-blocking hooks: `asyncio.create_task(handler)` — no await
- `asyncio.TimeoutError` → log warning, record failed execution, continue chain unchanged
- `HookAbortError` → return `HookChainResult(aborted=True, abort_reason=...)` immediately; no further handlers invoked
- Records execution outcome (success/failure) in hook execution log for every executed hook
- `HookChainResult.handlers_executed` ≤ total active hooks for event_type and tenant

**Testing requirements:**
- Unit test: two hooks with priorities 10 and 50 — lower priority hook called first
- Unit test: blocking hook returning modified payload — next hook receives mutated payload
- Unit test: non-blocking hook — chain does not await it
- Unit test: blocking hook times out — warning logged, chain continues with unmodified payload
- Unit test: `HookAbortError` in hook — chain stops, `aborted=True`, subsequent hooks not called
- Property test: `handlers_executed` in any `HookChainResult` ≤ count of registered active hooks
- Property test: hooks always execute in strictly ascending priority order

**Validates:** Req 7.2–7.12

---

## Phase 4 — Agent Runtime

---

### Task 4.1 — Implement `AgentRuntimeServiceImpl.create_agent` `[BE]`
**Estimate:** 45 min
**Deps:** 1.10, 1.5
**Files:**
- `+` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- `create_agent(config, tenant_id)` persists `Agent` with `status=IDLE` and `tenant_id` from request
- Raises `ValidationError` if `config.model` is empty or `config.memory_scopes` is empty
- Returns persisted `Agent`

**Testing requirements:**
- Unit test (mock repo): created agent has `status=IDLE` and correct `tenant_id`
- Property test: for any valid `AgentConfig` and `TenantId`, result always has `status=IDLE` and `tenant_id` matches input

**Validates:** Req 1.1, 1.2


---

### Task 4.2 — Implement system prompt resolution `[BE]`
**Estimate:** 1 h
**Deps:** 4.1
**Files:**
- `+` `backend/src/aetheros/infrastructure/langfuse/langfuse_tracing_service.py`
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- `_resolve_system_prompt(config)` fetches prompt from Langfuse if `system_prompt_id` is set
- Falls back to `system_prompt_text` if Langfuse fetch fails or `system_prompt_id` is `None`
- Raises `ValidationError` before creating `AgentSession` if neither resolves to non-empty content

**Testing requirements:**
- Unit test (mock Langfuse): `system_prompt_id` set and resolved — returns Langfuse content
- Unit test: `system_prompt_id` set but Langfuse fails — returns inline `system_prompt_text`
- Unit test: both `None` — raises `ValidationError`

**Validates:** Req 2.7, 14.2, 14.3, 14.4

---

### Task 4.3 — Implement initial message list builder and token trimmer `[BE]`
**Estimate:** 1 h
**Deps:** 4.2, 2.3
**Files:**
- `+` `backend/src/aetheros/application/agents/message_builder.py`

**Validation criteria:**
- `build_initial_messages(agent, input, session)` returns list ordered: `[SystemMessage, ...memory_context, ...history, HumanMessage]`
- Trims list to fit within `AgentConfig.context_window_tokens` using LangChain token trimmer
- `HumanMessage` is always the last element after trimming

**Testing requirements:**
- Unit test: output list always starts with `SystemMessage` and ends with `HumanMessage`
- Unit test: list with token count > `context_window_tokens` is trimmed to fit
- Property test: for any valid inputs, `messages[0]` is `SystemMessage` and `messages[-1]` is `HumanMessage`

**Validates:** Req 2.1, 2.2

---

### Task 4.4 — Implement `start_agent` — session lifecycle and hook integration `[BE]`
**Estimate:** 1.5 h
**Deps:** 4.3, 3.2
**Files:**
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- Raises `ConflictError` if agent status is `RUNNING` or `PAUSED`
- Creates `AgentSession` with `status=RUNNING`
- Emits `PRE_AGENT_RUN` hook; raises `AgentRunAbortedError` if `hook_result.aborted=True`
- Starts Langfuse trace; records `trace_id` on session
- On success: emits `POST_AGENT_RUN`, sets `status=COMPLETED`, persists `ended_at`
- On unhandled exception: emits `AGENT_ERROR`, sets `status=FAILED`, persists error and `ended_at`
- On timeout: raises `AgentTimeoutError`, sets `status=FAILED`, emits `AGENT_ERROR`
- `ended_at` always set when session reaches any terminal status

**Testing requirements:**
- Unit test: start on `RUNNING` agent raises `ConflictError`
- Unit test: `PRE_AGENT_RUN` abort → `AgentRunAbortedError` raised, no session persisted as `RUNNING`
- Unit test: successful completion → `status=COMPLETED`, `ended_at` set, `POST_AGENT_RUN` emitted
- Unit test: exception during execution → `status=FAILED`, `AGENT_ERROR` emitted
- Property test: `ended_at` is set if and only if status is terminal (`COMPLETED`, `FAILED`, `CANCELLED`)

**Validates:** Req 1.3, 1.4, 1.6, 1.7, 1.8, 1.9, 1.10, 1.16, 2.3, 2.8, 23.3

---

### Task 4.5 — Implement agent iteration loop with LangGraph `[BE]`
**Estimate:** 1.5 h
**Deps:** 4.4
**Files:**
- `+` `backend/src/aetheros/infrastructure/llm/langgraph_runtime.py`
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- LangGraph `astream` drives execution; each iteration emits `POST_LLM_CALL` hook after LLM response
- Tool calls dispatched through `ToolRegistryService`; `ToolResult` stored as `SESSION`-scoped `MemoryEntry`
- `iteration_count` incremented each loop; loop exits when `iteration_count == max_iterations`
- Each `AgentOutputChunk` published to Redis pub/sub channel `session:{session_id}:output`
- Loop invariant: `iteration_count ≤ max_iterations` at all times

**Testing requirements:**
- Unit test (mock LangGraph): tool call in response triggers `execute_tool` and memory store
- Unit test: reaching `max_iterations` stops loop and sets `status=COMPLETED` or `FAILED`
- Property test: `iteration_count` in persisted session never exceeds `max_iterations`

**Validates:** Req 1.11, 2.3, 2.4, 2.5, 2.10


---

### Task 4.6 — Implement `stop_agent`, `list_agents`, `stream_agent_output` `[BE]`
**Estimate:** 1 h
**Deps:** 4.5
**Files:**
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- `stop_agent(agent_id)` sets session `status=CANCELLED` and persists `ended_at`
- `list_agents(tenant_id, filters)` returns paginated `Page[Agent]` scoped to tenant with filter support
- `stream_agent_output(session_id)` returns `AsyncIterator[AgentOutputChunk]` subscribed to Redis channel `session:{session_id}:output`

**Testing requirements:**
- Unit test: `stop_agent` on running session → `CANCELLED` status and `ended_at` set
- Unit test: `list_agents` only returns agents for the specified tenant
- Unit test (mock Redis pub/sub): `stream_agent_output` yields chunks as they are published

**Validates:** Req 1.5, 1.12, 1.15

---

### Task 4.7 — Implement human-in-the-loop: pause and resume `[BE]`
**Estimate:** 1 h
**Deps:** 4.5
**Files:**
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`

**Validation criteria:**
- When LangGraph interrupt detected: session `status=WAITING_FOR_HUMAN`, publishes `awaiting_human:{session_id}` to Redis
- `inject_human_feedback(session_id, feedback)` resumes `WAITING_FOR_HUMAN` session via LangGraph `resume()`
- Raises `ConflictError` if session is not `WAITING_FOR_HUMAN`
- Session status transitions: `WAITING_FOR_HUMAN → RUNNING` on resume

**Testing requirements:**
- Unit test: interrupt detected → `status=WAITING_FOR_HUMAN`, Redis publish called
- Unit test: `inject_human_feedback` on non-waiting session raises `ConflictError`
- Unit test: `inject_human_feedback` on waiting session resumes LangGraph execution

**Validates:** Req 1.13, 1.14, 2.6

---

### Task 4.8 — Implement agent session state machine validation `[BE]`
**Estimate:** 45 min
**Deps:** 4.7
**Files:**
- `+` `backend/src/aetheros/domain/agents/state_machine.py`

**Validation criteria:**
- `validate_transition(current_status, new_status)` allows only: `IDLE→RUNNING`, `RUNNING→COMPLETED/FAILED/CANCELLED/WAITING_FOR_HUMAN`, `WAITING_FOR_HUMAN→RUNNING/CANCELLED`
- Raises `ConflictError` if current status is already terminal
- All service methods call this before persisting status changes

**Testing requirements:**
- Unit tests: all valid transitions pass; all invalid transitions raise `ConflictError`
- Unit test: `COMPLETED → RUNNING` raises `ConflictError`
- Property test: for any terminal status, any further transition always raises `ConflictError`

**Validates:** Req 23.1, 23.2, 23.4

---

## Phase 5 — Workflow Orchestration

---

### Task 5.1 — Implement `LangGraphRuntime.build_graph` `[BE]`
**Estimate:** 1.5 h
**Deps:** 4.7
**Files:**
- `~` `backend/src/aetheros/infrastructure/llm/langgraph_runtime.py`

**Validation criteria:**
- Builds `StateGraph` from `WorkflowDefinition`; adds all node types: `AGENT`, `TOOL`, `CONDITION`, `HUMAN_INPUT`, `PARALLEL`, `WAIT`, `START`, `END`
- Unconditional edges added with `graph.add_edge`; conditional groups use `graph.add_conditional_edges` with sandboxed router (`__builtins__={}`)
- Compiled graph cached in Redis by key `graph:{workflow_id}:{version}`; cache hit skips recompilation
- `PostgresSaver` used as checkpointer

**Testing requirements:**
- Unit test: valid `WorkflowDefinition` compiles without error
- Unit test: subsequent call with same workflow returns cached graph (compile not called again)
- Unit test: graph has entry point set to the `START` node

**Validates:** Req 8.4, 8.5, 8.17, 19.2


---

### Task 5.2 — Implement `condition_router` and `human_input_node` `[BE]`
**Estimate:** 1 h
**Deps:** 5.1
**Files:**
- `~` `backend/src/aetheros/infrastructure/llm/langgraph_runtime.py`

**Validation criteria:**
- `condition_router(state)` evaluates pre-compiled bytecode conditions against `AgentState` in sandboxed namespace; returns matching edge label
- No condition matches and no default edge → raises `RoutingError`
- Default edge (condition=`None`) used when no other condition matches
- `human_input_node` calls `interrupt()` then populates `state["human_feedback"]` on resume

**Testing requirements:**
- Unit test: condition matching first expression returns its label
- Unit test: condition matching second expression (not first) returns second label
- Unit test: no match with no default → `RoutingError`
- Unit test: no match with default → returns default label

**Validates:** Req 8.6, 8.7

---

### Task 5.3 — Implement `WorkflowService` — create and validate `[BE]`
**Estimate:** 1 h
**Deps:** 5.1, 1.10
**Files:**
- `+` `backend/src/aetheros/application/workflows/workflow_service.py`

**Validation criteria:**
- `create_workflow(definition, tenant_id)` validates: exactly one `START` node, exactly one `END` node, all edge source/target IDs reference defined node IDs
- Raises `ValidationError` (not persisted) if structural validation fails
- Persists `Workflow` with `version=1`, `is_active=True`

**Testing requirements:**
- Unit test: definition with two `START` nodes raises `ValidationError`
- Unit test: edge referencing unknown node ID raises `ValidationError`
- Unit test: valid definition persists with `version=1` and `is_active=True`

**Validates:** Req 8.1, 8.2, 8.3

---

### Task 5.4 — Implement `WorkflowService` — run, checkpoint, and node hooks `[BE]`
**Estimate:** 1.5 h
**Deps:** 5.3
**Files:**
- `~` `backend/src/aetheros/application/workflows/workflow_service.py`

**Validation criteria:**
- `run_workflow(workflow_id, input_data)` creates `WorkflowRun` in `PENDING` status, compiles graph, begins async execution
- `RunState` checkpointed to PostgreSQL at each node boundary via `PostgresSaver`
- `AGENT` node invokes `AgentRuntimeService.start_agent` with node `agent_id` and input
- Emits `WORKFLOW_NODE_ENTER` and `WORKFLOW_NODE_EXIT` hooks at every node
- `CONDITION` node raises `RoutingError` → sets run `status=FAILED`
- `HUMAN_INPUT` node: sets `status=WAITING_FOR_HUMAN`, persists `RunState`, attempts Redis publish (proceeds even if publish fails)

**Testing requirements:**
- Unit test: `run_workflow` creates `WorkflowRun` with `PENDING` then `RUNNING` status
- Unit test: `AGENT` node completion triggers next node
- Unit test: `RoutingError` in `CONDITION` node → run `status=FAILED`
- Unit test: Redis publish failure on `HUMAN_INPUT` does not abort workflow

**Validates:** Req 8.4, 8.5, 8.8, 8.9, 8.15

---

### Task 5.5 — Implement pause/resume/cancel workflow run `[BE]`
**Estimate:** 1 h
**Deps:** 5.4
**Files:**
- `~` `backend/src/aetheros/application/workflows/workflow_service.py`

**Validation criteria:**
- `pause_run(run_id)` sets status `PAUSED` on `RUNNING` run and persists `RunState`
- `resume_run(run_id, resume_data)` restores `RunState` from checkpoint and continues from paused node
- `cancel_run(run_id)` sets status `CANCELLED` and persists final state
- Terminal status runs (`COMPLETED`, `FAILED`, `CANCELLED`) reject any further transition with `ConflictError`
- `completed_at` set if and only if status is `COMPLETED`, `FAILED`, or `CANCELLED`

**Testing requirements:**
- Unit test: pause on `RUNNING` → `PAUSED`; resume → `RUNNING`
- Unit test: cancel on terminal status → `ConflictError`
- Unit test: `completed_at` is `None` for non-terminal; set for all terminal statuses
- Property test: `completed_at` is set iff status is terminal

**Validates:** Req 8.10, 8.11, 8.12, 8.13, 8.14, 9.1, 9.2, 9.3, 9.4


---

## Phase 6 — MCP Gateway

---

### Task 6.1 — Implement `MCPClientImpl` — connect and tool discovery `[BE]`
**Estimate:** 1.5 h
**Deps:** 2.5
**Files:**
- `+` `backend/src/aetheros/infrastructure/mcp/mcp_client.py`

**Validation criteria:**
- `connect(endpoint, auth)` opens JSON-RPC 2.0 transport: stdio subprocess, SSE, or WebSocket
- Sends `initialize` request; receives server capabilities
- Calls `tools/list`; registers each returned `MCPTool` into `ToolRegistryService` as `ToolType.MCP`
- Returns `MCPSession`
- `disconnect()` unregisters all tools registered from that session; keeps session active until all cleanup completes

**Testing requirements:**
- Unit test (mock transport): `connect` sends `initialize` then `tools/list`
- Unit test: `disconnect` unregisters all tools registered from this session
- Integration test: connect to a local mock MCP server over stdio, list tools, disconnect

**Validates:** Req 10.1, 10.2, 10.4, 10.5, 10.6

---

### Task 6.2 — Implement `MCPClientImpl` — tool call proxy `[BE]`
**Estimate:** 1 h
**Deps:** 6.1
**Files:**
- `~` `backend/src/aetheros/infrastructure/mcp/mcp_client.py`

**Validation criteria:**
- `call_tool(session_id, tool_name, arguments)` sends `tools/call` JSON-RPC request to external server
- Returns `MCPToolResult` on success
- MCP error response → returns `ToolResult(success=False, error=server_error_message)`

**Testing requirements:**
- Unit test (mock transport): successful tool call returns correct `MCPToolResult`
- Unit test: MCP error response surfaces as `ToolResult(success=False)`

**Validates:** Req 10.3, 10.7

---

### Task 6.3 — Implement `AetherOSMCPServer` `[BE]`
**Estimate:** 1.5 h
**Deps:** 4.5, 2.3, 5.4, 2.5
**Files:**
- `+` `backend/src/aetheros/infrastructure/mcp/mcp_server.py`

**Validation criteria:**
- Exposes tool categories: `agents/*`, `memory/*`, `workflows/*`, `tools/*`
- `handle_tools_list` returns all exposed tools
- `handle_tools_call` routes to correct AetherOS service and returns MCP response
- `handle_resources_list`, `handle_resources_read`, `handle_prompts_list`, `handle_prompts_get` implemented
- `stop_server()` closes all active connections cleanly; if called while still starting, proceeds with stop immediately

**Testing requirements:**
- Unit test: `tools/list` returns at least one tool per category
- Unit test: `tools/call` for `agents/run` delegates to `AgentRuntimeService`
- Unit test: `stop_server()` called before startup completes does not hang

**Validates:** Req 11.1–11.6

---

### Task 6.4 — Implement `MCPGatewayService` wiring `[BE]`
**Estimate:** 45 min
**Deps:** 6.2, 6.3
**Files:**
- `+` `backend/src/aetheros/application/mcp/mcp_gateway_service.py`

**Validation criteria:**
- Implements `MCPGatewayService` Protocol from design section 3.6
- Delegates `connect_mcp_client`, `disconnect_mcp_client`, `call_mcp_tool`, `list_mcp_tools` to `MCPClientImpl`
- Delegates `start_mcp_server`, `stop_mcp_server` to `AetherOSMCPServer`

**Testing requirements:**
- Unit test (mock client and server): all methods delegate correctly to underlying implementations

**Validates:** Req 10.1, 10.6, 11.4


---

## Phase 7 — Observability & Security

---

### Task 7.1 — Implement `LangfuseTracingService` `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.2
**Files:**
- `~` `backend/src/aetheros/infrastructure/langfuse/langfuse_tracing_service.py`

**Validation criteria:**
- `start_trace(name, metadata)` creates Langfuse trace; returns `trace_id` string
- `log_generation(trace_id, model, prompt, completion, usage, latency_ms)` creates a Langfuse `Generation` nested under trace
- `log_span(trace_id, name, input, output)` creates a Langfuse `Span` nested under trace
- `end_trace(trace_id, output, error)` closes trace with output and any error details
- `submit_eval(trace_id, evaluator, score, comment)` stores `EvalResult`; score must be in `[0.0, 1.0]`
- `create_prompt_version` and `resolve_prompt(prompt_id)` implemented

**Testing requirements:**
- Unit test (mock Langfuse SDK): `start_trace` returns a string trace ID
- Unit test: `log_generation` called within active trace creates nested generation
- Unit test: `submit_eval` with score > 1.0 raises `ValidationError`

**Validates:** Req 12.1, 12.2, 12.3, 12.4, 14.1

---

### Task 7.2 — Implement `CostTrackingService` `[BE]`
**Estimate:** 1 h
**Deps:** 1.10
**Files:**
- `+` `backend/src/aetheros/application/observability/cost_tracking_service.py`

**Validation criteria:**
- `record_llm_cost(tenant_id, session_id, model, usage)` creates `CostRecord`; `cost_usd >= 0`, `total_tokens >= 0`
- `get_cost_summary(tenant_id, since, until)` aggregates `CostRecord`s and returns totals grouped by model
- `check_budget_limit(tenant_id)` compares accumulated cost against tier limit; returns `BudgetStatus`
- FREE tier monthly token budget enforced

**Testing requirements:**
- Unit test (mock repo): `record_llm_cost` creates record with non-negative values
- Unit test: `get_cost_summary` sums correctly across multiple models
- Unit test: FREE tier at budget limit returns `BudgetStatus.EXCEEDED`
- Property test: for any valid usage input, `CostRecord.cost_usd >= 0` and `total_tokens >= 0`

**Validates:** Req 13.1–13.5

---

### Task 7.3 — Implement OpenTelemetry and Prometheus instrumentation `[BE]`
**Estimate:** 1 h
**Deps:** 1.17
**Files:**
- `+` `backend/src/aetheros/infrastructure/observability/metrics.py`
- `~` `backend/src/aetheros/main.py`

**Validation criteria:**
- FastAPI auto-instrumented via `opentelemetry-instrumentation-fastapi`
- All 10 Prometheus metrics registered: `aetheros_agent_runs_total`, `aetheros_agent_run_duration_seconds`, `aetheros_llm_tokens_total`, `aetheros_llm_cost_usd_total`, `aetheros_tool_calls_total`, `aetheros_memory_entries_total`, `aetheros_workflow_runs_total`, `aetheros_hook_executions_total`, `aetheros_api_requests_total`, `aetheros_api_request_duration_seconds`
- `GET /metrics` endpoint returns Prometheus text format

**Testing requirements:**
- Unit test: each metric counter/histogram is registered in the default registry
- Integration test: `GET /metrics` returns HTTP 200 with `aetheros_api_requests_total` present

**Validates:** Req 12.5, 12.6

---

### Task 7.4 — Implement immutable audit log `[BE]`
**Estimate:** 1 h
**Deps:** 1.10
**Files:**
- `+` `backend/src/aetheros/infrastructure/persistence/postgres/audit_log_repository.py`
- `+` `backend/alembic/versions/0002_audit_log.py`

**Validation criteria:**
- `audit_entries` table has columns: `id`, `tenant_id`, `action`, `resource_type`, `resource_id`, `actor_id`, `payload`, `created_at`
- `created_at` column has no `UPDATE` trigger; application code has no `update` or `delete` method on this repository
- `write_entry(action, resource_type, resource_id, actor_id, payload)` inserts record
- All `create`, `update`, `delete` operations in service layer call `write_entry`

**Testing requirements:**
- Unit test: `write_entry` inserts a record; no update method exists on `AuditLogRepository`
- Integration test: after calling `write_entry`, querying by `resource_id` returns the entry with unchanged content

**Validates:** Req 19.5


---

### Task 7.5 — Implement `PromptInjectionGuard` hook handler `[BE]`
**Estimate:** 1 h
**Deps:** 3.2
**Files:**
- `+` `backend/src/aetheros/application/hooks/handlers/prompt_injection_guard.py`

**Validation criteria:**
- Registered as a blocking hook on `PRE_LLM_CALL` event
- Inspects `payload["prompt"]` for injection patterns (e.g., `ignore previous instructions`, `system:`, role-overriding patterns)
- Raises `HookAbortError` with descriptive reason if injection detected
- Returns unmodified payload if no injection detected

**Testing requirements:**
- Unit test: payload containing `"ignore previous instructions"` → `HookAbortError` raised
- Unit test: benign payload → payload returned unchanged
- Unit test: guard is registered as blocking hook on `PRE_LLM_CALL`

**Validates:** Req 19.1

---

### Task 7.6 — Implement tenant isolation validation in service layer `[BE]`
**Estimate:** 1 h
**Deps:** 4.1, 5.3
**Files:**
- `+` `backend/src/aetheros/domain/shared/tenant_guard.py`
- `~` `backend/src/aetheros/application/agents/agent_runtime_service.py`
- `~` `backend/src/aetheros/application/workflows/workflow_service.py`
- `~` `backend/src/aetheros/application/memory/memory_service.py`
- `~` `backend/src/aetheros/application/tools/tool_registry_service.py`

**Validation criteria:**
- `assert_tenant_owns(entity_tenant_id, request_tenant_id)` raises `PermissionDeniedError` if they differ
- Every entity access in all service methods calls this guard before operating on the entity
- No service method bypasses the guard

**Testing requirements:**
- Unit test: accessing agent owned by tenant A using tenant B's context → `PermissionDeniedError`
- Integration test: create entities for T1 and T2; T1's list query returns zero T2 entities
- Property test: for any two distinct tenant IDs, `assert_tenant_owns` always raises `PermissionDeniedError`

**Validates:** Req 15.2, 15.3

---

## Phase 8 — REST API Layer

---

### Task 8.1 — Implement Pydantic request/response schemas `[BE]`
**Estimate:** 1.5 h
**Deps:** 1.5, 1.6
**Files:**
- `+` `backend/src/aetheros/api/schemas/agents.py`
- `+` `backend/src/aetheros/api/schemas/workflows.py`
- `+` `backend/src/aetheros/api/schemas/memory.py`
- `+` `backend/src/aetheros/api/schemas/tools.py`
- `+` `backend/src/aetheros/api/schemas/hooks.py`
- `+` `backend/src/aetheros/api/schemas/auth.py`
- `+` `backend/src/aetheros/api/schemas/mcp.py`
- `+` `backend/src/aetheros/api/schemas/observability.py`

**Validation criteria:**
- Every REST endpoint has a dedicated Pydantic v2 `BaseModel` for request body and response
- All schemas use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- No domain entities exposed directly in API responses — always serialized through schemas

**Testing requirements:**
- Unit test: each request schema rejects invalid payloads with Pydantic `ValidationError`
- Unit test: each response schema serializes the corresponding domain entity correctly

**Validates:** Req 18.5

---

### Task 8.2 — Implement Agent Runtime API router `[BE]`
**Estimate:** 1.5 h
**Deps:** 8.1, 4.6, 4.7
**Files:**
- `+` `backend/src/aetheros/api/v1/agents.py`
- `+` `backend/src/aetheros/api/v1/sessions.py`

**Validation criteria:**
- `POST /api/v1/agents` → `create_agent` → HTTP 201
- `GET /api/v1/agents` → `list_agents` with pagination → HTTP 200
- `GET /api/v1/agents/{agent_id}` → HTTP 200 or 404
- `POST /api/v1/agents/{agent_id}/run` → `start_agent` → HTTP 202
- `POST /api/v1/agents/{agent_id}/stop` → `stop_agent` → HTTP 200
- `POST /api/v1/sessions/{session_id}/feedback` → `inject_human_feedback` → HTTP 200
- `GET /api/v1/sessions/{session_id}` → HTTP 200 or 404
- WebSocket `WS /api/v1/sessions/{session_id}/stream` — authenticated with same JWT/API key as REST; delivers `AgentOutputChunk` JSON events

**Testing requirements:**
- Integration test: `POST /api/v1/agents` without auth returns HTTP 401
- Integration test: `POST /api/v1/agents/{id}/run` returns HTTP 202 and creates session
- Integration test: WebSocket connect without auth → connection closed with 401

**Validates:** Req 18.1, 18.2, 18.3


---

### Task 8.3 — Implement Workflow, Memory, Tools, Plugins, Hooks API routers `[BE]`
**Estimate:** 1.5 h
**Deps:** 8.1, 5.5, 2.4, 2.7, 3.2
**Files:**
- `+` `backend/src/aetheros/api/v1/workflows.py`
- `+` `backend/src/aetheros/api/v1/memory.py`
- `+` `backend/src/aetheros/api/v1/tools.py`
- `+` `backend/src/aetheros/api/v1/hooks.py`

**Validation criteria:**
- Workflows: `POST /api/v1/workflows`, `POST /api/v1/workflows/{id}/run`, `POST /api/v1/runs/{id}/pause`, `POST /api/v1/runs/{id}/resume`, `POST /api/v1/runs/{id}/cancel`, `GET /api/v1/runs/{id}`
- Memory: `POST /api/v1/memory/store`, `POST /api/v1/memory/retrieve`, `DELETE /api/v1/memory/{entry_id}`, `POST /api/v1/memory/consolidate`
- Tools: `POST /api/v1/tools`, `DELETE /api/v1/tools/{tool_id}`, `GET /api/v1/tools`, `POST /api/v1/tools/{tool_id}/execute`
- Plugins: `POST /api/v1/plugins`, `POST /api/v1/plugins/{id}/enable`, `POST /api/v1/plugins/{id}/disable`, `DELETE /api/v1/plugins/{id}`
- Hooks: `POST /api/v1/hooks`, `DELETE /api/v1/hooks/{id}`, `GET /api/v1/hooks/{id}/executions`

**Testing requirements:**
- Integration test: each router's primary CRUD endpoints return correct status codes
- Integration test: all routers return HTTP 401 without auth

**Validates:** Req 18.1

---

### Task 8.4 — Implement Auth, Observability, MCP, and Tenant API routers `[BE]`
**Estimate:** 1 h
**Deps:** 8.1, 7.1, 7.2, 6.4, 1.11, 1.14
**Files:**
- `+` `backend/src/aetheros/api/v1/auth.py`
- `+` `backend/src/aetheros/api/v1/tenants.py`
- `+` `backend/src/aetheros/api/v1/observability.py`
- `+` `backend/src/aetheros/api/v1/mcp.py`

**Validation criteria:**
- Auth: `POST /api/v1/auth/token` (JWT), `POST /api/v1/auth/api-keys`, `DELETE /api/v1/auth/api-keys/{id}`
- Tenants: `POST /api/v1/tenants`, `GET /api/v1/tenants/{id}`
- Observability: `GET /api/v1/observability/costs`, `GET /api/v1/observability/traces`, `POST /api/v1/observability/evals`
- MCP: `POST /api/v1/mcp/connect`, `DELETE /api/v1/mcp/sessions/{id}`, `GET /api/v1/mcp/sessions/{id}/tools`

**Testing requirements:**
- Integration test: `POST /api/v1/auth/api-keys` returns raw key once only (key not re-retrievable)
- Integration test: `GET /api/v1/observability/costs` returns correct aggregated data

**Validates:** Req 18.1, 16.7

---

## Phase 9 — Frontend

---

### Task 9.1 — Initialize Vite + React + TailwindCSS project `[FE]`
**Estimate:** 1 h
**Deps:** none
**Files:**
- `+` `frontend/package.json`
- `+` `frontend/vite.config.ts`
- `+` `frontend/tailwind.config.ts`
- `+` `frontend/tsconfig.json`
- `+` `frontend/src/main.tsx`
- `+` `frontend/src/App.tsx`

**Validation criteria:**
- `npm run dev` starts dev server without errors
- `npm run build` produces `dist/` with no TypeScript errors
- All declared packages installed: `react`, `react-dom`, `@tanstack/react-query`, `zustand`, `axios`, `reactflow`, `recharts`, `@radix-ui/*`
- TailwindCSS directives present in global CSS

**Testing requirements:**
- Smoke test: `npm run build` exits with code 0

**Validates:** Req 21.1

---

### Task 9.2 — Implement Axios client, Zustand auth store, JWT interceptor `[FE]`
**Estimate:** 1 h
**Deps:** 9.1
**Files:**
- `+` `frontend/src/shared/api/client.ts`
- `+` `frontend/src/shared/stores/authStore.ts`
- `+` `frontend/src/shared/stores/tenantStore.ts`

**Validation criteria:**
- Axios instance has base URL from env var `VITE_API_BASE_URL`
- Request interceptor attaches `Authorization: Bearer {token}` from `authStore`
- If token absent, interceptor blocks request (does not send unauthenticated request)
- `authStore` exposes `token`, `setToken()`, `clearToken()`

**Testing requirements:**
- Unit test (vitest): interceptor adds `Authorization` header when token present
- Unit test: interceptor throws/cancels request when token absent

**Validates:** Req 21.5, 21.7


---

### Task 9.3 — Implement `useAgentStream` WebSocket hook `[FE]`
**Estimate:** 1.5 h
**Deps:** 9.2
**Files:**
- `+` `frontend/src/shared/hooks/useAgentStream.ts`
- `+` `frontend/src/shared/components/StreamingOutput.tsx`

**Validation criteria:**
- Connects to `ws://{host}/api/v1/sessions/{id}/stream` with JWT as query param or header
- Calls `onChunk(chunk)` for each received `AgentOutputChunk` JSON message
- On disconnect: shows "reconnecting" status; retries with exponential backoff (max 5 retries)
- After max retries exhausted: shows "disconnected" status; stops retrying
- On successful reconnect: hides reconnecting indicator; resumes streaming

**Testing requirements:**
- Unit test (vitest + mock WebSocket): disconnect triggers reconnect attempt with correct status transitions
- Unit test: after 5 failed retries, status is `"disconnected"` and no further retries occur
- Unit test: successful reconnect after 2 failures → status returns to `"connected"`

**Validates:** Req 21.2, 21.6

---

### Task 9.4 — Implement Agent Management views `[FE]`
**Estimate:** 1.5 h
**Deps:** 9.3
**Files:**
- `+` `frontend/src/features/agents/AgentList.tsx`
- `+` `frontend/src/features/agents/AgentDetail.tsx`
- `+` `frontend/src/features/agents/AgentRunPanel.tsx`
- `+` `frontend/src/features/agents/AgentConfigForm.tsx`

**Validation criteria:**
- `AgentList` fetches agents with TanStack Query; displays paginated table with status badges
- `AgentDetail` shows agent config, current status, and link to active session
- `AgentRunPanel` renders `StreamingOutput` component for active session with real-time chunks
- `AgentConfigForm` submits `POST /api/v1/agents` and invalidates query cache on success
- TanStack Query used for all data fetching with automatic cache invalidation

**Testing requirements:**
- Unit test (React Testing Library): `AgentList` renders agents returned by mocked query
- Unit test: `AgentConfigForm` submit calls correct API endpoint

**Validates:** Req 21.1, 21.4

---

### Task 9.5 — Implement Workflow Editor with React Flow `[FE]`
**Estimate:** 1.5 h
**Deps:** 9.2
**Files:**
- `+` `frontend/src/features/workflows/WorkflowEditor.tsx`
- `+` `frontend/src/features/workflows/WorkflowRunDetail.tsx`
- `+` `frontend/src/features/workflows/WorkflowList.tsx`

**Validation criteria:**
- `WorkflowEditor` renders `ReactFlow` canvas with draggable nodes and connectable edges
- Node types: AGENT, TOOL, CONDITION, HUMAN_INPUT, PARALLEL, WAIT, START, END rendered with distinct visuals
- Save button serializes graph to `WorkflowDefinition` format and calls `POST /api/v1/workflows`
- `WorkflowRunDetail` shows run status, current node, and timeline of completed nodes

**Testing requirements:**
- Unit test: serializing a two-node graph produces valid `WorkflowDefinition` JSON
- Unit test: `WorkflowRunDetail` renders correct status badge for each `RunStatus`

**Validates:** Req 21.3

---

### Task 9.6 — Implement remaining dashboard views `[FE]`
**Estimate:** 1.5 h
**Deps:** 9.2
**Files:**
- `+` `frontend/src/features/memory/MemoryExplorer.tsx`
- `+` `frontend/src/features/tools/ToolRegistry.tsx`
- `+` `frontend/src/features/tools/PluginManager.tsx`
- `+` `frontend/src/features/observability/CostDashboard.tsx`
- `+` `frontend/src/features/observability/TraceViewer.tsx`
- `+` `frontend/src/features/observability/EvalDashboard.tsx`
- `+` `frontend/src/features/settings/TenantSettings.tsx`
- `+` `frontend/src/features/settings/UserManagement.tsx`
- `+` `frontend/src/features/settings/ApiKeys.tsx`

**Validation criteria:**
- `CostDashboard` renders `Recharts` line chart of `cost_usd` over time, grouped by model
- `MemoryExplorer` shows paginated memory entries with scope filter dropdown
- `PluginManager` shows installed plugins with enable/disable toggle
- `ApiKeys` shows key list (masked values) with create and revoke actions
- All views use TanStack Query for data fetching

**Testing requirements:**
- Unit test: `CostDashboard` renders chart without errors given mock cost data
- Unit test: `ApiKeys` does not display raw key value after initial creation response

**Validates:** Req 21.1


---

## Phase 10 — Infrastructure

---

### Task 10.1 — Write `docker-compose.yml` `[INF]`
**Estimate:** 1.5 h
**Deps:** none
**Files:**
- `+` `docker-compose.yml`
- `+` `docker-compose.dev.yml`

**Validation criteria:**
- Defines all 11 services: `api`, `worker`, `frontend`, `postgres`, `redis`, `langfuse`, `otel`, `prometheus`, `grafana`, `loki`, `promtail`
- `api` service depends on `postgres` and `redis` with `healthcheck`
- `api` entrypoint runs `alembic upgrade head` before starting uvicorn; exits non-zero on migration failure
- All secrets provided via environment variable references (no hardcoded values)
- `docker compose up` starts all services and `api` passes health check at `GET /api/v1/health`

**Testing requirements:**
- Manual verification: `docker compose up -d && curl http://localhost:8000/api/v1/health` returns `{"status": "ok"}`
- CI check: `docker compose config` validates without errors

**Validates:** Req 24.1, 24.2

---

### Task 10.2 — Write Dockerfile for API and frontend `[INF]`
**Estimate:** 1 h
**Deps:** 1.1, 9.1
**Files:**
- `+` `backend/Dockerfile`
- `+` `frontend/Dockerfile`
- `+` `backend/.dockerignore`
- `+` `frontend/.dockerignore`

**Validation criteria:**
- API `Dockerfile` uses multi-stage build: `builder` (installs deps) → `prod` (copies built artifacts); runs as non-root user
- Frontend `Dockerfile` builds Vite app and serves via Nginx
- `docker build --target prod backend/` succeeds with no errors
- Final image does not contain dev dependencies or source `.env` files

**Testing requirements:**
- CI: `docker build` step in pipeline exits code 0

**Validates:** Req 24.3

---

### Task 10.3 — Implement GitHub Actions CI pipeline `[INF]`
**Estimate:** 1.5 h
**Deps:** 10.2
**Files:**
- `+` `.github/workflows/ci.yml`

**Validation criteria:**
- `lint` job: runs `ruff check .`, `black --check .`, `mypy src/`; fails pipeline if any check fails
- `test` job: runs `pytest --cov=src --cov-report=xml` with minimum coverage threshold
- `e2e` job: `docker compose up -d && pytest tests/e2e`
- `build` job: builds production Docker image
- `scan` job: runs `trivy image` vulnerability scan; fails on CRITICAL severity findings
- All jobs run on `push` to `main` and `pull_request`

**Testing requirements:**
- Pipeline itself is the test; verify each job completes without error on a clean commit

**Validates:** Req 24.3

---

### Task 10.4 — Write Kubernetes manifests and Helm chart `[INF]`
**Estimate:** 1.5 h
**Deps:** 10.2
**Files:**
- `+` `infra/k8s/api-deployment.yaml`
- `+` `infra/k8s/api-service.yaml`
- `+` `infra/k8s/worker-deployment.yaml`
- `+` `infra/k8s/configmap.yaml`
- `+` `infra/k8s/secrets.yaml`
- `+` `infra/helm/Chart.yaml`
- `+` `infra/helm/values.yaml`
- `+` `infra/helm/templates/`

**Validation criteria:**
- `api` and `worker` deployments are stateless with `replicas: 2` as default
- All secrets loaded from Kubernetes `Secret` objects (no plaintext in manifests)
- `helm lint infra/helm/` passes with no errors
- `kubectl apply --dry-run=client -f infra/k8s/` passes

**Testing requirements:**
- `helm lint` and `kubectl apply --dry-run=client` in CI

**Validates:** Req 24.4, 24.5


---

## Phase 11 — End-to-End Tests

---

### Task 11.1 — E2E: Full agent run `[BE]`
**Estimate:** 1.5 h
**Deps:** 8.2, 10.1
**Files:**
- `+` `backend/tests/e2e/test_agent_run.py`

**Validation criteria:**
- Creates tenant and agent via REST API
- Calls `POST /api/v1/agents/{id}/run`; connects WebSocket stream
- Asserts at least one `AgentOutputChunk` received
- Asserts session status is `COMPLETED` after stream closes

**Testing requirements:**
- Runs against live `docker compose` stack
- Must pass in CI `e2e` job

**Validates:** Req 1.3, 1.12

---

### Task 11.2 — E2E: Workflow with conditional branching `[BE]`
**Estimate:** 1.5 h
**Deps:** 8.3, 10.1
**Files:**
- `+` `backend/tests/e2e/test_workflow_conditional.py`

**Validation criteria:**
- Defines workflow with two branches via `CONDITION` node
- Runs workflow with inputs that route to each branch in separate test cases
- Asserts `WorkflowRun.status == COMPLETED` for both branches
- Asserts correct branch was taken via `current_node_id` in `RunState`

**Testing requirements:**
- Both branches exercised in separate test runs

**Validates:** Req 8.6, 8.7

---

### Task 11.3 — E2E: Human-in-the-loop workflow `[BE]`
**Estimate:** 1 h
**Deps:** 8.3, 10.1
**Files:**
- `+` `backend/tests/e2e/test_human_in_the_loop.py`

**Validation criteria:**
- Runs workflow containing `HUMAN_INPUT` node
- Asserts run reaches `WAITING_FOR_HUMAN` status
- Calls `POST /api/v1/runs/{id}/resume` with feedback data
- Asserts run completes to `COMPLETED`

**Testing requirements:**
- Test covers full pause → resume → complete cycle

**Validates:** Req 8.9, 8.10

---

### Task 11.4 — E2E: Plugin install and tool execution `[BE]`
**Estimate:** 1 h
**Deps:** 8.3, 10.1
**Files:**
- `+` `backend/tests/e2e/test_plugin_lifecycle.py`

**Validation criteria:**
- Uploads valid plugin manifest via `POST /api/v1/plugins`
- Enables plugin; asserts declared tools appear in `GET /api/v1/tools`
- Executes a plugin tool via `POST /api/v1/tools/{id}/execute`; asserts `ToolResult.success=True`
- Disables plugin; asserts tools no longer appear in listing
- Uninstalls plugin; asserts plugin removed

**Testing requirements:**
- Test uses a bundled stub plugin with a no-op tool

**Validates:** Req 6.4, 6.6, 6.8

---

## Phase 12 — Documentation

---

### Task 12.1 — Write project README `[DOC]`
**Estimate:** 1 h
**Deps:** 10.1
**Files:**
- `+` `README.md`

**Validation criteria:**
- Covers: project overview, quickstart with `docker compose up`, environment variable table, architecture diagram (Mermaid), link to design doc

**Testing requirements:**
- `docker compose up` command in README runs without modification

**Validates:** Req 24.1

---

### Task 12.2 — Write API reference documentation `[DOC]`
**Estimate:** 1 h
**Deps:** 8.4
**Files:**
- `+` `docs/api-reference.md`

**Validation criteria:**
- Documents every endpoint with: method, path, auth requirements, request schema, response schema, error codes
- FastAPI's auto-generated OpenAPI spec at `/docs` is accurate and matches this document

**Testing requirements:**
- Verify `/docs` endpoint returns HTTP 200 with valid OpenAPI JSON

**Validates:** Req 18.1


---

## Task Dependency Graph

```
Phase 1 (Foundation)
  1.1 → 1.2 → 1.3
  1.1 → 1.4 → 1.5 → 1.7
  1.1 → 1.6
  1.7, 1.8 → 1.9 → 1.10
  1.10 → 1.11, 1.12
  1.12 → 1.13 → 1.14
  1.2 → 1.15, 1.16
  1.13, 1.14, 1.15 → 1.17

Phase 2 (Memory & Tools)
  1.5 → 2.1
  1.10 → 2.2
  2.1, 2.2 → 2.3 → 2.4
  1.10 → 2.5 → 2.6 → 2.7

Phase 3 (Hook Engine)
  1.10, 1.16 → 3.1 → 3.2

Phase 4 (Agent Runtime)
  1.10, 1.5 → 4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6
  4.5 → 4.7 → 4.8

Phase 5 (Workflow)
  4.7 → 5.1 → 5.2
  5.1, 1.10 → 5.3 → 5.4 → 5.5

Phase 6 (MCP Gateway)
  2.5 → 6.1 → 6.2
  4.5, 2.3, 5.4, 2.5 → 6.3
  6.2, 6.3 → 6.4

Phase 7 (Observability & Security)
  1.2 → 7.1
  1.10 → 7.2
  1.17 → 7.3
  1.10 → 7.4
  3.2 → 7.5
  4.1, 5.3 → 7.6

Phase 8 (REST API)
  1.5, 1.6 → 8.1 → 8.2 → 8.3 → 8.4

Phase 9 (Frontend)
  9.1 → 9.2 → 9.3 → 9.4
  9.2 → 9.5
  9.2 → 9.6

Phase 10 (Infrastructure)
  10.1 (standalone)
  1.1, 9.1 → 10.2 → 10.3 → 10.4

Phase 11 (E2E Tests)
  8.2, 10.1 → 11.1
  8.3, 10.1 → 11.2, 11.3, 11.4

Phase 12 (Documentation)
  10.1 → 12.1
  8.4 → 12.2
```

---

## Summary

| Phase | Tasks | Type | Est. Hours |
|---|---|---|---|
| 1 — Foundation | 1.1–1.17 | BE + INF | ~20 h |
| 2 — Memory & Tools | 2.1–2.7 | BE | ~9 h |
| 3 — Hook Engine | 3.1–3.2 | BE | ~2.5 h |
| 4 — Agent Runtime | 4.1–4.8 | BE | ~9.5 h |
| 5 — Workflow | 5.1–5.5 | BE | ~6.5 h |
| 6 — MCP Gateway | 6.1–6.4 | BE | ~5 h |
| 7 — Observability & Security | 7.1–7.6 | BE | ~6 h |
| 8 — REST API Layer | 8.1–8.4 | BE | ~5 h |
| 9 — Frontend | 9.1–9.6 | FE | ~8.5 h |
| 10 — Infrastructure | 10.1–10.4 | INF | ~5.5 h |
| 11 — E2E Tests | 11.1–11.4 | BE | ~5 h |
| 12 — Documentation | 12.1–12.2 | DOC | ~2 h |
| **Total** | **55 tasks** | | **~84 h** |

> All tasks are scoped to ≤ 2 hours. Tasks marked `[BE]` must pass `ruff`, `black`, and `mypy` before merging. Property-based tests use `hypothesis`. Integration tests require a running PostgreSQL + Redis instance (provided by `docker compose`).
