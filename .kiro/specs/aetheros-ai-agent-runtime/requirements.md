# Requirements Document

## Introduction

AetherOS is a production-grade, modular AI Operating System that orchestrates multiple AI agents with
shared memory, tools, plugins, hooks, tracing, and workflow automation. The platform is organized into
eight bounded contexts: Agent Runtime, Memory, Tool & Plugin Registry, Hook Engine, Workflow
Orchestration, Observability, Tenant & Identity, and MCP Gateway. It exposes a FastAPI backend with
WebSocket streaming, a React/Vite frontend dashboard, a Python SDK, and a CLI — all built on Clean
Architecture with Domain-Driven Design principles, async-first Python 3.13, PostgreSQL + pgvector,
and Redis.

These requirements are derived directly from the approved design document and capture the functional
and non-functional obligations each bounded context must satisfy.

---

## Glossary

- **Agent**: An autonomous AI entity configured with a model, system prompt, tools, and memory scopes, owned by a Tenant.
- **AgentSession**: A single execution run of an Agent, tracking status, iteration count, inputs, outputs, and trace linkage.
- **AgentRuntimeService**: The application service responsible for creating, starting, stopping, and streaming Agent executions.
- **Workflow**: A directed graph of nodes (AGENT, TOOL, CONDITION, HUMAN_INPUT, PARALLEL, WAIT, START, END) that orchestrates multi-step AI processes.
- **WorkflowRun**: A single execution instance of a Workflow, persisted as a RunState via LangGraph checkpointing.
- **WorkflowService**: The application service that manages Workflow definitions and their execution runs.
- **MemoryService**: The application service providing four-scoped persistent and ephemeral memory with semantic vector search.
- **MemoryEntry**: A stored unit of memory (message, tool_call, observation, summary, fact, document) with optional pgvector embedding.
- **MemoryScope**: The isolation boundary for memory entries — SESSION, AGENT, TENANT, or GLOBAL.
- **EmbeddingService**: The infrastructure adapter that converts text to vector embeddings for semantic search.
- **ToolRegistryService**: The application service for registering, discovering, and executing tools of types BUILTIN, MCP, PLUGIN, or CUSTOM.
- **Tool**: A registered, executable capability with a typed parameter schema, handler reference, and tenant scope.
- **ToolCall**: A single invocation request targeting a Tool, carrying arguments and caller session context.
- **ToolResult**: The outcome of a ToolCall, including success flag, output, error, execution time, and optional token cost.
- **Plugin**: A packaged extension containing tool definitions and hook definitions, installed per tenant via a manifest.
- **PluginManifest**: A JSON schema-validated descriptor declaring a Plugin's identity, version, tools, hooks, permissions, and entry point.
- **HookEngineService**: The application service that registers lifecycle hooks and executes priority-ordered hook chains on events.
- **Hook**: A registered handler for a specific HookEventType, with configurable priority, blocking mode, timeout, and JSONLogic condition.
- **HookEvent**: A lifecycle occurrence emitted within the platform carrying a typed payload and correlation ID.
- **HookChain**: The ordered sequence of Hooks executed for a single HookEvent emission.
- **HookChainResult**: The outcome of a HookChain execution, including final payload, abort status, and handler count.
- **MCPGatewayService**: The application service managing bidirectional MCP integration — AetherOS as both MCP server and MCP client.
- **MCPServer**: The AetherOS component exposing agents, memory, workflows, and tools to external MCP-compatible LLM clients.
- **MCPClient**: The AetherOS component connecting to external MCP servers and registering their tools into the ToolRegistryService.
- **MCPSession**: An active connection between MCPClient and an external MCP server.
- **ObservabilityService**: The cross-cutting service providing OpenTelemetry traces, Langfuse LLM observability, Prometheus metrics, Loki logs, and cost tracking.
- **CostRecord**: A persisted record of LLM token usage and USD cost, scoped to tenant, session, and run.
- **EvalResult**: A scored evaluation of an AgentSession produced by an evaluator against defined criteria.
- **PromptVersion**: A versioned system prompt managed in Langfuse, referenced by Agent configurations.
- **AuthService**: The service authenticating requests via JWT (RS256) or HMAC-SHA256 API keys.
- **Tenant**: An isolated organizational unit with a tier (FREE, PRO, ENTERPRISE), owning all platform resources.
- **User**: A human principal belonging to a Tenant, assigned a role of admin, member, or viewer.
- **ApiKey**: A tenant-scoped credential stored only as a bcrypt hash, used for service-account authentication.
- **RateLimiter**: The Redis token-bucket enforcing per-tenant request and LLM call rate limits.
- **FeatureFlagService**: The Redis-backed service evaluating runtime feature toggles.
- **Container**: The dependency-injector DI container that wires the object graph at application startup.
- **CorrelationId**: A unique identifier propagated through all layers of a request for tracing and log correlation.

---

## Requirements

---

### Requirement 1: Agent Lifecycle Management

**User Story:** As a tenant operator, I want to create, configure, start, stop, and monitor AI agents,
so that I can deploy and manage autonomous AI workers within my organization.

#### Acceptance Criteria

1. WHEN a tenant provides an AgentConfig with a valid model, name, and at least one memory scope, THE AgentRuntimeService SHALL create a new Agent entity and persist it with status IDLE.
2. WHEN an agent is created, THE AgentRuntimeService SHALL associate the Agent with the requesting Tenant's TenantId.
3. WHEN a start request is received for an Agent with status IDLE or COMPLETED, THE AgentRuntimeService SHALL create a new AgentSession with status RUNNING and begin execution.
4. IF a start request is received for an Agent whose status is RUNNING or PAUSED, THEN THE AgentRuntimeService SHALL return a ConflictError without creating a duplicate session.
5. WHEN a stop request is received for a running AgentSession, THE AgentRuntimeService SHALL transition the Agent's status to CANCELLED and persist the ended_at timestamp.
6. WHEN an AgentSession is started, THE AgentRuntimeService SHALL emit a PRE_AGENT_RUN HookEvent and apply any payload mutations returned by the HookChain before proceeding.
7. IF the PRE_AGENT_RUN HookChain specifically returns aborted=True, THEN THE AgentRuntimeService SHALL raise an AgentRunAbortedError and not start execution; hook aborts from other event types SHALL NOT raise an AgentRunAbortedError.
8. WHEN an AgentSession completes successfully, THE AgentRuntimeService SHALL emit a POST_AGENT_RUN HookEvent, persist the final output, and set status to COMPLETED.
9. WHEN an AgentSession fails due to an unhandled exception, THE AgentRuntimeService SHALL emit an AGENT_ERROR HookEvent, persist the error message, and set status to FAILED.
10. WHEN an AgentSession exceeds the AgentConfig.timeout_seconds, THE AgentRuntimeService SHALL raise an AgentTimeoutError, set status to FAILED, and emit an AGENT_ERROR HookEvent.
11. WHEN an AgentSession's iteration_count reaches AgentConfig.max_iterations, THE AgentRuntimeService SHALL stop the loop and set status to COMPLETED or FAILED based on final state.
12. WHEN a client requests streaming output for an active AgentSession, THE AgentRuntimeService SHALL deliver an AsyncIterator of AgentOutputChunk events over WebSocket.
13. WHEN the Agent requires human input during execution, THE AgentRuntimeService SHALL transition the session status to WAITING_FOR_HUMAN and publish an awaiting_human event to Redis.
14. WHEN human feedback is injected into a WAITING_FOR_HUMAN session, THE AgentRuntimeService SHALL resume execution with the provided HumanFeedback.
15. THE AgentRuntimeService SHALL support listing agents for a tenant with pagination and filter parameters.
16. WHEN an AgentSession ends (any terminal status), THE AgentRuntimeService SHALL record the ended_at timestamp and persist the final AgentSession state.

---

### Requirement 2: Agent Execution Loop & LangGraph Integration

**User Story:** As a platform engineer, I want agent execution to be driven by a LangGraph StateGraph
with bounded iteration, tool dispatch, and human-in-the-loop support, so that agents behave
predictably and safely under all input conditions.

#### Acceptance Criteria

1. WHEN an AgentSession is started, THE AgentRuntimeService SHALL construct an initial message list in the order: SystemMessage, relevant memory context, conversation history, HumanMessage.
2. WHEN the initial message list is built, THE AgentRuntimeService SHALL trim it to fit within the AgentConfig.context_window_tokens limit using a token trimmer.
3. WHEN the LangGraph runtime executes an agent iteration, THE AgentRuntimeService SHALL emit a POST_LLM_CALL HookEvent after each LLM response is received.
4. WHEN the LLM response contains tool calls, THE AgentRuntimeService SHALL dispatch each call through the ToolRegistryService and store the ToolResult as a SESSION-scoped MemoryEntry; session MemoryEntries for tool results may also be stored when no tool call was dispatched if the session state indicates a tool result is present.
5. WHILE an AgentSession is RUNNING, THE AgentRuntimeService SHALL maintain the loop invariant that iteration_count ≤ AgentConfig.max_iterations.
6. WHEN the LangGraph runtime detects a HUMAN_INPUT node, THE AgentRuntimeService SHALL call LangGraph interrupt() to pause execution and await resume with HumanFeedback.
7. WHEN an AgentSession requires a system prompt, THE AgentRuntimeService SHALL resolve it from Langfuse by system_prompt_id if set, otherwise fall back to the inline system_prompt_text.
8. WHEN a new AgentSession is started, THE AgentRuntimeService SHALL start a Langfuse trace and record the trace_id on the AgentSession.
9. WHEN an AgentSession ends, THE AgentRuntimeService SHALL call end_trace on Langfuse with the session output and any error details.
10. WHEN agent output is produced during execution, THE AgentRuntimeService SHALL publish each AgentOutputChunk to the Redis pub/sub channel for WebSocket delivery.

---

### Requirement 3: Memory Storage and Retrieval

**User Story:** As an agent developer, I want agents to store and semantically retrieve memories
across four isolation scopes, so that agents can maintain context, accumulate knowledge, and share
information appropriately within and across sessions.

#### Acceptance Criteria

1. THE MemoryService SHALL support four memory scopes: SESSION (ephemeral, single run), AGENT (persists across sessions), TENANT (shared across all tenant agents), and GLOBAL (platform-wide, read-only).
2. WHEN a MemoryEntry is stored, THE MemoryService SHALL persist it to the PostgreSQL memory_entries table scoped by the provided MemoryScope.
3. WHEN a retrieval query is received with a non-empty text and no pre-computed embedding, THE MemoryService SHALL compute an embedding via the EmbeddingService before querying.
4. WHEN performing vector search, THE MemoryService SHALL query pgvector using cosine similarity and return at most top_k MemoryEntries belonging to the specified scope.
5. WHEN re-ranking retrieved MemoryEntries, THE MemoryService SHALL apply a recency decay formula combining cosine similarity (weight 0.85) and recency factor (weight 0.15) with decay rate 0.01 per hour.
6. FOR ALL MemoryEntries returned by retrieve(), THE MemoryService SHALL ensure each entry's relevance_score is in the range [0.0, 1.0].
7. WHEN a retrieval query includes entry_type filters, THE MemoryService SHALL exclude entries whose entry_type is not in the filter list.
8. WHEN a retrieval query includes metadata filters, THE MemoryService SHALL apply them after the initial vector search candidate selection.
9. WHEN consolidate_long_term is called with strategy SUMMARIZE, THE MemoryService SHALL produce an LLM-generated narrative summary and persist it as a SUMMARY-type MemoryEntry in AGENT scope.
10. WHEN consolidate_long_term is called with strategy EXTRACT_FACTS, THE MemoryService SHALL produce individual FACT-type MemoryEntries in AGENT scope from the LLM fact extraction.
11. WHEN consolidate_long_term is called with strategy DEDUPLICATE, THE MemoryService SHALL cluster session entries by embedding similarity and retain the centroid of each cluster in AGENT scope.
12. WHEN consolidation completes, THE MemoryService SHALL delete all SESSION-scoped entries for the given agent_id.
13. IF consolidate_long_term is called and there are no source entries, THEN THE MemoryService SHALL return without creating any new entries or deleting existing entries.
14. WHEN a delete request is received for a MemoryEntryId, THE MemoryService SHALL remove that entry from persistent storage.
15. WHEN clear_scope is called for a MemoryScope, THE MemoryService SHALL delete all MemoryEntries belonging to that scope.
16. WHEN get_session_history is called, THE MemoryService SHALL return all MemoryEntries for the given SessionId in chronological order.

---

### Requirement 4: Memory Serialization and Embedding Round-Trip

**User Story:** As a platform engineer, I want memory entries and their embeddings to be stored and
retrieved without data loss, so that semantic search accuracy is preserved across system restarts
and consolidation cycles.

#### Acceptance Criteria

1. WHEN a MemoryEntry with an embedding is persisted and then retrieved by ID, THE MemoryService SHALL return a MemoryEntry whose embedding vector is equivalent to the originally stored vector.
2. WHEN an embedding is computed for a text string and then used to retrieve MemoryEntries, THE MemoryService SHALL return the stored entry matching that text as the top result when it exists in the scope.
3. THE EmbeddingService SHALL return an Embedding with dimensions equal to the declared model's output size for any non-empty input text.
4. FOR ALL valid MemoryEntry objects, storing then retrieving by scope SHALL produce an entry with identical content, entry_type, scope, and metadata fields.

---

### Requirement 5: Tool Registration and Discovery

**User Story:** As an agent developer, I want to register, discover, and manage tools of multiple
types, so that agents can access the full range of platform capabilities and external integrations.

#### Acceptance Criteria

1. WHEN a ToolDefinition is registered, THE ToolRegistryService SHALL persist the Tool with its namespaced ToolId, parameter schema, handler reference, and tenant scope.
2. WHEN a tool is registered with tenant_id=None, THE ToolRegistryService SHALL treat it as a platform-wide tool available to all tenants.
3. WHEN a tool is unregistered, THE ToolRegistryService SHALL remove it from the registry and prevent future calls from resolving it.
4. WHEN listing tools with filters, THE ToolRegistryService SHALL return only tools that match all provided filter criteria and are accessible to the requesting tenant.
5. WHEN a ToolCall is submitted, THE ToolRegistryService SHALL validate that the call.arguments conform to the tool's parameter schema before dispatching.
6. IF a ToolCall's arguments fail schema validation, THEN THE ToolRegistryService SHALL raise a ValidationError without invoking the handler, except when the handler's context is required for error handling — in that case the handler may be invoked before the ValidationError is raised.
7. IF a ToolCall references a ToolId that does not exist or is not enabled for the tenant, THEN THE ToolRegistryService SHALL raise a NotFoundError.
8. WHEN a ToolCall is dispatched to a BUILTIN tool, THE ToolRegistryService SHALL invoke the registered builtin handler with the call arguments and ExecutionContext.
9. WHEN a ToolCall is dispatched to an MCP tool, THE ToolRegistryService SHALL proxy the call through the MCPGatewayService to the appropriate external MCP server.
10. WHEN a ToolCall is dispatched to a PLUGIN tool, THE ToolRegistryService SHALL invoke the plugin loader with the plugin_id, tool_id, and arguments.
11. WHEN a ToolCall is dispatched to a CUSTOM tool, THE ToolRegistryService SHALL dynamically load and call the handler referenced by handler_ref.
12. WHEN a tool execution completes successfully, THE ToolRegistryService SHALL return a ToolResult with success=True and the execution_time_ms recorded.
13. WHEN a tool execution raises a ToolExecutionError, THE ToolRegistryService SHALL return a ToolResult with success=False and the error message captured.
14. WHEN a ToolCall is executed, THE ToolRegistryService SHALL emit PRE_TOOL_CALL and POST_TOOL_CALL HookEvents with the call and result payloads respectively.

---

### Requirement 6: Plugin Installation and Management

**User Story:** As a tenant administrator, I want to install, enable, disable, and uninstall plugins
that extend the platform with new tools and hooks, so that my organization can customize agent
capabilities without modifying core platform code.

#### Acceptance Criteria

1. WHEN a PluginManifest is submitted for installation, THE ToolRegistryService SHALL validate the manifest against the PLUGIN_MANIFEST_SCHEMA before accepting it.
2. IF a PluginManifest fails schema validation, THEN THE ToolRegistryService SHALL reject the installation and return a ValidationError with the specific violations.
3. WHEN a plugin manifest is validated successfully, THE ToolRegistryService SHALL persist the Plugin in Inactive state and associate it with the requesting Tenant.
4. WHEN a tenant enables a Plugin, THE ToolRegistryService SHALL transition it to Active state and register all tools declared in its manifest into the ToolRegistryService.
5. WHEN a Plugin is activated, THE ToolRegistryService SHALL register all hooks declared in its manifest with the HookEngineService.
6. WHEN a tenant disables a Plugin, THE ToolRegistryService SHALL transition it to Inactive state and unregister all its tools and hooks.
7. WHEN a new plugin version is uploaded, THE ToolRegistryService SHALL perform the upgrade and roll back to the previous Active version if the upgrade fails.
8. WHEN a plugin is uninstalled, THE ToolRegistryService SHALL remove it and all its registered tools and hooks from the platform.
9. THE ToolRegistryService SHALL enforce plugin permissions declared in the manifest at runtime, preventing access to capabilities not listed in the permissions array.
10. WHEN a plugin is installed, THE ToolRegistryService SHALL validate that all permission strings are members of the allowed permission set: memory:read, memory:write, tools:execute, agents:read, http:outbound.

---

### Requirement 7: Hook Engine — Event Registration and Chain Execution

**User Story:** As a platform integrator, I want to register lifecycle hooks that execute in
priority order on platform events, so that I can intercept, modify, audit, and control agent
and tool behavior without changing core platform logic.

#### Acceptance Criteria

1. WHEN a HookDefinition is registered, THE HookEngineService SHALL persist the Hook with its event_type, handler_ref, priority, blocking flag, timeout_ms, retry_count, and JSONLogic condition.
2. WHEN an event is emitted, THE HookEngineService SHALL load all active Hooks matching the event_type from a Redis cache; the cache TTL SHALL default to 30 seconds but proceed with any configured TTL value.
3. WHEN filtering hooks for an event, THE HookEngineService SHALL include only Hooks that are active, match the tenant_id or are platform-wide, and whose JSONLogic condition evaluates to true against the event payload.
4. WHEN executing a HookChain, THE HookEngineService SHALL invoke handlers in ascending priority order (lower priority value = earlier execution).
5. WHEN a blocking Hook executes, THE HookEngineService SHALL await its completion within timeout_ms and merge its returned payload into the chain's running payload after the await completes.
6. WHEN a non-blocking Hook executes, THE HookEngineService SHALL dispatch it as a fire-and-forget asyncio task without waiting for its result.
7. WHEN a blocking Hook exceeds its timeout_ms, THE HookEngineService SHALL log a warning, record a failed execution, and continue the chain with the unmodified payload.
8. WHEN a Hook handler raises HookAbortError, THE HookEngineService SHALL stop the chain, set aborted=True, capture the abort_reason, and return the HookChainResult immediately.
9. WHEN a HookChain completes, THE HookEngineService SHALL return a HookChainResult containing the final payload, handlers_executed count, aborted flag, abort_reason, and execution_time_ms.
10. FOR ALL HookChainResults, THE HookEngineService SHALL ensure handlers_executed is less than or equal to the number of registered active hooks for that event_type and tenant.
11. WHEN a hook execution completes (success or failure), THE HookEngineService SHALL record the execution outcome in the hook execution log.
12. THE HookEngineService SHALL support all twelve event types: PRE_AGENT_RUN, POST_AGENT_RUN, PRE_TOOL_CALL, POST_TOOL_CALL, PRE_LLM_CALL, POST_LLM_CALL, AGENT_ERROR, HUMAN_INPUT_REQUIRED, WORKFLOW_NODE_ENTER, WORKFLOW_NODE_EXIT, MEMORY_WRITE, and MEMORY_READ.
13. WHEN a hook is unregistered, THE HookEngineService SHALL remove it from the registry and invalidate the relevant cache entries.
14. WHEN queried for execution history, THE HookEngineService SHALL return HookExecution records for the specified hook_id filtered by the since timestamp.

---

### Requirement 8: Workflow Orchestration

**User Story:** As a workflow designer, I want to define, run, pause, resume, and cancel directed
graph workflows composed of agent, tool, condition, and human-input nodes, so that I can automate
complex multi-step AI processes with branching logic and human oversight.

#### Acceptance Criteria

1. WHEN a WorkflowDefinition is submitted, THE WorkflowService SHALL validate that it contains exactly one START node, exactly one END node, and that all edge source and target IDs reference defined nodes.
2. IF a WorkflowDefinition fails structural validation, THEN THE WorkflowService SHALL return a ValidationError and not persist the Workflow.
3. WHEN a Workflow is created, THE WorkflowService SHALL persist it with version=1 and is_active=True.
4. WHEN a workflow is run, THE WorkflowService SHALL create a WorkflowRun in PENDING status, compile the LangGraph StateGraph from the definition, and begin asynchronous execution.
5. WHEN the LangGraph StateGraph executes, THE WorkflowService SHALL checkpoint the RunState to PostgreSQL at each node boundary before transitioning to the next node.
6. WHEN a CONDITION node is reached during execution, THE WorkflowService SHALL evaluate the pre-compiled edge condition expressions against the current RunState and route to the matching target node.
7. IF no edge condition matches and no default edge exists for a CONDITION node, THEN THE WorkflowService SHALL raise a RoutingError and set the WorkflowRun status to FAILED.
8. WHEN an AGENT node is executed, THE WorkflowService SHALL invoke the AgentRuntimeService.start_agent with the node's agent_id and node input data.
9. WHEN a HUMAN_INPUT node is reached, THE WorkflowService SHALL pause the WorkflowRun, set status to WAITING_FOR_HUMAN, persist the RunState, and attempt to publish an awaiting_human event to Redis; workflow execution SHALL proceed even if the Redis event publish fails.
10. WHEN resume_run is called on a WAITING_FOR_HUMAN WorkflowRun, THE WorkflowService SHALL restore the checkpointed RunState and continue execution from the paused node with the provided resume_data.
11. WHEN pause_run is called on a RUNNING WorkflowRun, THE WorkflowService SHALL set status to PAUSED and persist the current RunState.
12. WHEN cancel_run is called, THE WorkflowService SHALL set the WorkflowRun status to CANCELLED and persist the final state.
13. WHEN a WorkflowRun completes successfully, THE WorkflowService SHALL set status to COMPLETED, record the completed_at timestamp, and persist the output_data; the status update and timestamp may be persisted independently such that one may succeed if the other fails.
14. WHEN a WorkflowRun fails, THE WorkflowService SHALL set status to FAILED, record the error, and persist the final RunState.
15. WHEN any node is entered or exited during execution, THE WorkflowService SHALL emit WORKFLOW_NODE_ENTER and WORKFLOW_NODE_EXIT HookEvents respectively.
16. THE WorkflowService SHALL support listing workflow runs with pagination and filter parameters.
17. WHEN a compiled StateGraph is requested for a Workflow version that has been compiled previously, THE WorkflowService SHALL return the cached graph from Redis.

---

### Requirement 9: Workflow State Machine Integrity

**User Story:** As a platform operator, I want workflow run status transitions to follow a strict
state machine, so that runs are never left in undefined states and their history is auditable.

#### Acceptance Criteria

1. THE WorkflowService SHALL allow status transitions only along the defined paths: PENDING → RUNNING; RUNNING → PAUSED, WAITING_FOR_HUMAN, COMPLETED, FAILED, or CANCELLED; PAUSED → RUNNING or CANCELLED; WAITING_FOR_HUMAN → RUNNING or CANCELLED. All workflows MUST pass through RUNNING before reaching a terminal status.
2. IF a WorkflowRun is in a terminal status (COMPLETED, FAILED, or CANCELLED), THEN THE WorkflowService SHALL reject any further status transition requests with a ConflictError.
3. WHEN a WorkflowRun transitions to any new status, THE WorkflowService SHALL persist the updated RunState with the new status and the updated_at timestamp.
4. FOR ALL WorkflowRun instances, THE WorkflowService SHALL ensure the completed_at field is set if and only if the status is COMPLETED, FAILED, or CANCELLED.

---

### Requirement 10: MCP Gateway — Client Integration

**User Story:** As an agent developer, I want AetherOS to connect to external MCP servers and
automatically register their tools, so that agents can use any MCP-compatible external capability
without manual tool configuration.

#### Acceptance Criteria

1. WHEN connect_mcp_client is called with an endpoint and auth credentials, THE MCPGatewayService SHALL open an MCP JSON-RPC 2.0 transport (stdio, SSE, or WebSocket), send an initialize request, and receive the server's capabilities.
2. WHEN an MCPSession is established, THE MCPGatewayService SHALL call tools/list on the external server and register each returned MCPTool into the ToolRegistryService as a ToolType.MCP tool.
3. WHEN a ToolCall targeting an MCP tool is executed, THE MCPGatewayService SHALL proxy the call as a tools/call JSON-RPC request to the connected external server and return the MCPToolResult.
4. WHEN a MCPSession is disconnected, THE MCPGatewayService SHALL unregister all tools that were registered from that session.
5. THE MCPGatewayService SHALL support listing all MCPTools available in an active MCPSession; tools remain listable until the session is fully disconnected even if the transport connection has closed.
6. WHEN disconnect_mcp_client is called, THE MCPGatewayService SHALL close the transport connection and clean up the MCPSession state; IF any cleanup operation fails, THEN THE MCPGatewayService SHALL keep the session active until all cleanup operations complete successfully.
7. IF an MCP server returns an error response for a tool call, THEN THE MCPGatewayService SHALL surface it as a ToolResult with success=False and the error message from the server response.

---

### Requirement 11: MCP Gateway — Server Exposure

**User Story:** As an external LLM client developer, I want to connect to AetherOS via the MCP
protocol and invoke its agents, memory, workflows, and tools as MCP tools, so that any MCP-compatible
client can leverage AetherOS capabilities without direct REST API integration.

#### Acceptance Criteria

1. WHEN the MCPServer is started, THE MCPGatewayService SHALL expose AetherOS capabilities as MCP-compatible tools in the categories: agents/*, memory/*, workflows/*, and tools/*.
2. WHEN an external client sends a tools/list request to the MCPServer, THE MCPGatewayService SHALL return a list of all exposed AetherOS MCP tools.
3. WHEN an external client sends a tools/call request to the MCPServer, THE MCPGatewayService SHALL route the call to the corresponding AetherOS service and return the result as an MCP response.
4. WHEN the MCPServer is stopped, THE MCPGatewayService SHALL close all active connections and release server resources; IF the stop operation is initiated while the server is still starting, THE MCPGatewayService SHALL proceed with the stop immediately without waiting for full startup to complete.
5. THE MCPGatewayService SHALL support MCP resources/list and resources/read endpoints for AetherOS-managed resources.
6. THE MCPGatewayService SHALL support MCP prompts/list and prompts/get endpoints for AetherOS-managed PromptVersions.

---

### Requirement 12: Observability — Tracing and LLM Telemetry

**User Story:** As a platform operator, I want every agent run and LLM call to be traced through
Langfuse and OpenTelemetry, so that I can diagnose failures, measure latency, and audit the full
execution path of any session.

#### Acceptance Criteria

1. WHEN an AgentSession begins, THE ObservabilityService SHALL create a Langfuse trace and associate the trace_id with the AgentSession.
2. WHEN each LLM call is made during a session, THE ObservabilityService SHALL record a Langfuse Generation with the model, prompt, completion, token usage, and latency_ms; generations with zero latency or zero token counts SHALL be recorded as-is.
3. WHEN a tool call is made during a session, THE ObservabilityService SHALL record a Langfuse Span nested under the active trace.
4. WHEN an AgentSession ends, THE ObservabilityService SHALL close the Langfuse trace with the final output and any error details.
5. WHEN a request is received by the API gateway, THE ObservabilityService SHALL generate a CorrelationId and propagate it through all downstream service calls, traces, and log entries for that request.
6. THE ObservabilityService SHALL emit the following Prometheus metrics: aetheros_agent_runs_total, aetheros_agent_run_duration_seconds, aetheros_llm_tokens_total, aetheros_llm_cost_usd_total, aetheros_tool_calls_total, aetheros_memory_entries_total, aetheros_workflow_runs_total, aetheros_hook_executions_total, aetheros_api_requests_total, and aetheros_api_request_duration_seconds.
7. WHEN an evaluation score is submitted for a session, THE ObservabilityService SHALL persist an EvalResult with the evaluator name, score in [0.0, 1.0], criteria, and optional reasoning.
8. THE ObservabilityService SHALL ship all application logs to Loki via Promtail for aggregation and querying in Grafana.

---

### Requirement 13: Cost Tracking and Budget Management

**User Story:** As a tenant administrator, I want to track LLM token usage and accumulated costs
per session, run, and time window, so that I can monitor spending and enforce budget limits.

#### Acceptance Criteria

1. WHEN an LLM call completes, THE ObservabilityService SHALL create a CostRecord capturing tenant_id, session_id, run_id, model, prompt_tokens, completion_tokens, total_tokens, and cost_usd.
2. FOR ALL CostRecords, THE ObservabilityService SHALL ensure cost_usd is greater than or equal to zero and total_tokens is greater than or equal to zero.
3. WHEN a cost summary is requested for a tenant and time window, THE ObservabilityService SHALL aggregate all CostRecords within that window and return the total tokens and cost_usd grouped by model.
4. WHEN budget limit checking is requested for a tenant, THE ObservabilityService SHALL compare the tenant's accumulated cost against the tier's budget limit and return a BudgetStatus indicating remaining capacity.
5. WHERE a tenant's tier is FREE, THE ObservabilityService SHALL enforce the FREE tier's monthly token budget limit via the budget check mechanism.

---

### Requirement 14: Prompt Version Management

**User Story:** As an AI engineer, I want to manage versioned system prompts in Langfuse and
reference them from agent configurations, so that prompt changes are tracked, reproducible,
and can be rolled back independently of agent deployments.

#### Acceptance Criteria

1. THE ObservabilityService SHALL support creating PromptVersions with a name, version string, content, variable list, model defaults, and active flag.
2. WHEN an AgentConfig references a system_prompt_id, THE AgentRuntimeService SHALL resolve the prompt content from Langfuse using that ID at session start.
3. WHEN a system_prompt_id is provided but cannot be resolved from Langfuse, THE AgentRuntimeService SHALL fall back to the inline system_prompt_text if set.
4. IF neither system_prompt_id resolves nor system_prompt_text is set, THEN THE AgentRuntimeService SHALL raise a ValidationError before creating the AgentSession.

---

### Requirement 15: Multi-Tenancy and Data Isolation

**User Story:** As a platform operator, I want all tenant data to be strictly isolated at both the
application and database levels, so that no tenant can access, modify, or even observe another
tenant's agents, sessions, workflows, memory, tools, or plugins.

#### Acceptance Criteria

1. THE platform SHALL enforce tenant isolation on all database tables through PostgreSQL Row-Level Security policies using the app.current_tenant_id session variable.
2. WHEN any service layer query is executed, THE platform SHALL validate the tenant_id ownership of every entity being accessed against the authenticated request's tenant_id.
3. FOR ALL database queries Q and distinct tenants T1 and T2, THE platform SHALL ensure the result set of Q for T1 contains no entities belonging to T2.
4. WHEN a Tenant is created, THE platform SHALL assign it a tier of FREE, PRO, or ENTERPRISE and apply the corresponding resource quotas and rate limits.
5. THE platform SHALL support three tenant tiers: FREE, PRO, and ENTERPRISE, each with distinct rate limits, memory limits, and feature access.
6. WHEN a request targets a resource belonging to a different tenant than the authenticated user's tenant, THE AuthService SHALL raise a PermissionDeniedError.

---

### Requirement 16: Authentication and Authorization

**User Story:** As a security administrator, I want all API requests to be authenticated via JWT
or API keys and authorized against RBAC roles, so that only permitted principals can perform
actions on platform resources.

#### Acceptance Criteria

1. WHEN a request includes a JWT Bearer token, THE AuthService SHALL validate the JWT using RS256 signature verification and extract the AuthContext.
2. WHEN a request includes an API key, THE AuthService SHALL hash the provided key with HMAC-SHA256, compare it against the stored bcrypt hash, and return the AuthContext if matched.
3. IF a request provides neither a valid JWT nor a valid API key, THEN THE AuthService SHALL reject the request with HTTP 401 and error code UNAUTHORIZED.
4. WHEN authorization is checked for an action, THE AuthService SHALL enforce RBAC rules: admin role has full CRUD on all tenant resources; member role can create and run agents and workflows and read all resources; viewer role has read-only access. Admin CRUD access SHALL still be denied when other security constraints are violated, such as expired tokens or invalid signatures.
5. IF a user's role does not permit the requested action on the target resource, THEN THE AuthService SHALL raise a PermissionDeniedError (HTTP 403).
6. THE platform SHALL store API key values only as bcrypt hashes; the raw API key SHALL never be written to the database, logs, or traces. Existing API key values SHALL not be retrievable through any subsequent API operation after initial creation.
7. WHEN an ApiKey is created, THE AuthService SHALL return the raw key value exactly once and never expose it again.
8. WHEN an ApiKey has an expires_at set and that timestamp has passed, THE AuthService SHALL reject authentication attempts using that key with HTTP 401.

---

### Requirement 17: Rate Limiting

**User Story:** As a platform operator, I want per-tenant rate limiting enforced on all API
endpoints and LLM calls via a Redis token bucket, so that no single tenant can degrade platform
performance for others.

#### Acceptance Criteria

1. WHEN an API request is received, THE RateLimiter SHALL check the requesting tenant's token bucket in Redis and allow the request only if sufficient tokens are available.
2. WHEN a request is allowed, THE RateLimiter SHALL decrement only the specific token bucket corresponding to the request type (API request bucket or LLM call bucket).
3. IF a tenant's token bucket is exhausted, THEN THE RateLimiter SHALL reject the request with HTTP 429 and error code RATE_LIMIT_EXCEEDED.
4. THE RateLimiter SHALL apply separate token buckets for API requests and LLM calls per tenant.
5. WHERE a tenant's tier is FREE, THE RateLimiter SHALL enforce the FREE tier's rate limits; WHERE a tenant's tier is PRO, THE RateLimiter SHALL enforce PRO tier limits; WHERE a tenant's tier is ENTERPRISE, THE RateLimiter SHALL enforce ENTERPRISE tier limits.
6. THE RateLimiter SHALL replenish token buckets at the configured refill rate per time window using Redis atomic operations, capping the replenishment so that the bucket total never exceeds the configured maximum capacity.

---

### Requirement 18: API Gateway and WebSocket Streaming

**User Story:** As a client developer, I want a FastAPI REST and WebSocket API that handles
authentication, rate limiting, and real-time streaming, so that I can integrate AetherOS into
any application using standard HTTP and WebSocket protocols.

#### Acceptance Criteria

1. THE platform SHALL expose a versioned REST API under the /api/v1/ path prefix covering all bounded context operations.
2. WHEN an agent session is started, THE platform SHALL expose a WebSocket endpoint at /api/v1/sessions/{id}/stream that delivers AgentOutputChunk JSON events as they are produced.
3. WHEN a WebSocket client connects to the stream endpoint, THE platform SHALL authenticate the connection using the same JWT or API key mechanism as REST endpoints.
4. WHEN the API gateway receives a request, THE platform SHALL attach a CorrelationId to the request and propagate it through all downstream service calls and log entries.
5. WHEN an unhandled AetherOSError is raised, THE platform SHALL return a structured JSON error response with the appropriate HTTP status code and error_code field as defined in the error mapping.
6. THE platform SHALL apply authentication middleware before rate limit middleware, and rate limit middleware before routing to application services; this ordering SHALL be enforced during both request processing and system initialization.

---

### Requirement 19: Security — Input Sanitization and Sandboxing

**User Story:** As a security engineer, I want all LLM prompts, tool arguments, and workflow
conditions to pass through security controls, so that the platform is protected against prompt
injection, SQL injection, and arbitrary code execution.

#### Acceptance Criteria

1. WHEN a PRE_LLM_CALL HookEvent is emitted, THE platform SHALL invoke a PromptInjectionGuard hook handler that inspects the prompt payload before it reaches the LLM provider.
2. WHEN workflow edge conditions are authored, THE platform SHALL compile them at authoring time into bytecode and evaluate them at runtime in a sandboxed namespace with __builtins__ set to an empty dict.
3. THE platform SHALL use parameterized queries exclusively for all database access, whether via SQLAlchemy ORM, a query builder, or any other database access method; raw SQL string construction from user-provided input is prohibited.
4. WHEN sensitive credentials (API keys, JWT signing secrets, database passwords) are required, THE platform SHALL read them from environment variables and never embed them in source code or configuration files committed to version control.
5. WHEN an audit log entry is created for a create, update, or delete operation, THE platform SHALL record it as an immutable entry that cannot be modified or deleted by application code.
6. THE platform SHALL encrypt all inter-service traffic with TLS and expose all external endpoints over HTTPS only.

---

### Requirement 20: Performance and Scalability

**User Story:** As a platform operator, I want all I/O to be fully asynchronous, connection-pooled,
and horizontally scalable, so that the platform handles concurrent agent runs without blocking and
scales to enterprise workloads.

#### Acceptance Criteria

1. THE platform SHALL use asyncpg as the PostgreSQL driver and perform all database operations via async/await, with a connection pool of minimum 5 and maximum 20 connections per API server instance.
2. THE platform SHALL use aioredis for all Redis operations with a dedicated connection pool.
3. WHEN a CPU-bound operation is required in a hot path, THE platform SHALL offload it to asyncio.run_in_executor to avoid blocking the event loop.
4. WHEN multiple MemoryEntries require embedding during consolidation, THE platform SHALL call EmbeddingService.embed_batch() to batch the embedding requests rather than issuing one call per entry.
5. WHEN a tool result is eligible for caching, THE platform SHALL store it in Redis with a TTL defined by the tool's metadata and return the cached result for identical subsequent calls within that TTL; if a cached result exists for a tool call that is no longer cache-eligible, THE platform SHALL return the cached result.
6. THE platform SHALL deploy stateless API server instances behind a load balancer, using Redis for all shared session state.
7. WHEN agent output is produced, THE platform SHALL stream it via WebSocket without buffering the full response server-side.
8. WHEN the pgvector index is queried, THE platform SHALL use the IVFFlat index on the memory_entries.embedding column with lists=100 for Phase 1 through Phase 3, upgrading to HNSW in Phase 4 and beyond.

---

### Requirement 21: Frontend Dashboard

**User Story:** As an agent operator, I want a React/Vite dashboard to manage agents, monitor
sessions, visualize workflows, explore memory, and view cost and evaluation data, so that I can
operate the platform without direct API access.

#### Acceptance Criteria

1. THE platform SHALL provide a React/Vite frontend dashboard accessible via a web browser that covers agent management, workflow management, memory exploration, tool/plugin management, and observability views.
2. WHEN an agent session is active, THE Dashboard SHALL display a real-time streaming output panel that renders AgentOutputChunk events progressively as they arrive over WebSocket.
3. WHEN a workflow is viewed in the editor, THE Dashboard SHALL render the workflow graph as an interactive visual node editor using React Flow.
4. WHEN the Dashboard loads agent or session data, THE Dashboard SHALL use TanStack Query for data fetching with automatic cache invalidation and re-fetching.
5. THE Dashboard SHALL manage authentication state (JWT token and tenant context) in a Zustand store and attach the token to all API requests via an Axios interceptor.
6. WHEN a WebSocket connection to a session stream is lost, THE Dashboard SHALL display a "reconnecting" status indicator during reconnection attempts; upon successful reconnection THE Dashboard SHALL resume streaming and hide the indicator; upon exhausting retries THE Dashboard SHALL display a "disconnected" status to the user.
7. WHEN the Axios interceptor cannot attach the JWT token to an API request due to configuration or timing issues, THE Dashboard SHALL block the request and not allow it to proceed without authentication.

---

### Requirement 22: Dependency Injection and Cross-Cutting Infrastructure

**User Story:** As a backend engineer, I want all services to receive dependencies through
constructor injection via a DI container, so that the object graph is deterministic, testable,
and can be rewired without modifying business logic.

#### Acceptance Criteria

1. THE platform SHALL use a dependency-injector Container class to wire all application services, repositories, and infrastructure adapters at startup.
2. THE platform SHALL never instantiate infrastructure adapters (database connections, Redis clients, HTTP clients) directly inside domain or application service code.
3. WHEN the Container is initialized, THE platform SHALL fail immediately if any required configuration values are missing; the Container SHALL not reach a partially-initialized state that accepts requests with missing configuration.
4. THE platform SHALL support a FeatureFlagService backed by Redis that evaluates boolean feature flags at runtime, allowing features to be toggled without redeployment.
5. WHEN a domain event is published, THE platform SHALL deliver it via an in-process async event bus; in distributed deployments, THE platform SHALL use Redis pub/sub for cross-service event delivery.

---

### Requirement 23: Agent Session Status State Machine

**User Story:** As a platform engineer, I want agent session status transitions to follow a strict
state machine with terminal states, so that sessions are never left in ambiguous states and
downstream hooks always receive a consistent status.

#### Acceptance Criteria

1. THE AgentRuntimeService SHALL allow AgentSession status transitions only along defined paths: IDLE → RUNNING; RUNNING → COMPLETED, FAILED, CANCELLED, or WAITING_FOR_HUMAN; WAITING_FOR_HUMAN → RUNNING or CANCELLED.
2. IF an AgentSession is in a terminal status (COMPLETED, FAILED, or CANCELLED), THEN THE AgentRuntimeService SHALL reject any further status transition with a ConflictError.
3. FOR ALL AgentSession instances, THE AgentRuntimeService SHALL ensure the ended_at field is set if and only if the status is COMPLETED, FAILED, or CANCELLED.
4. WHEN an AgentSession transitions to any new status, THE AgentRuntimeService SHALL persist the updated session immediately.

---

### Requirement 24: Infrastructure and Deployment

**User Story:** As a DevOps engineer, I want the entire platform to run as a Docker Compose stack
for local development and be deployable to Kubernetes for production, so that the platform is
reproducible across environments.

#### Acceptance Criteria

1. THE platform SHALL define a docker-compose.yml that starts the following services: api, worker, frontend, postgres, redis, langfuse, otel, prometheus, grafana, loki, and promtail.
2. WHEN the docker-compose stack starts, THE platform SHALL apply all database migrations via Alembic before the API server accepts requests; IF migrations fail during startup, THEN THE API server SHALL refuse to start.
3. THE platform SHALL maintain a CI pipeline that runs ruff, black, and mypy linting checks; unit and integration tests with coverage reporting; E2E tests via docker compose; a production Docker image build; and a Trivy vulnerability scan.
4. THE platform SHALL provide Kubernetes manifests and a Helm chart for production deployment as part of Phase 7 deliverables.
5. THE platform SHALL manage all secrets (database passwords, API keys, JWT signing keys) via environment variables, with Kubernetes Secrets or AWS Secrets Manager in production environments.
