from __future__ import annotations

from collections.abc import AsyncGenerator

from aetheros.application.hooks.hook_engine_service import HookEngineService
from aetheros.application.langgraph.runtime_api import (
    ExecutionChunk,
    ExecutionResult,
    WorkflowRuntime,
)
from aetheros.domain.hooks.models import HookEventType
from aetheros.domain.shared.exceptions import ConflictError, ValidationError
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import WorkflowDefinition, WorkflowRun


class WorkflowService:
    """Manage workflow definitions and execution runs."""

    def __init__(
        self,
        hook_engine: HookEngineService | None = None,
        workflow_runtime: WorkflowRuntime | None = None,
    ) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._runs: dict[str, WorkflowRun] = {}
        self._hook_engine = hook_engine
        self._workflow_runtime = workflow_runtime

    def _validate_definition(self, definition: WorkflowDefinition) -> None:
        if not definition.name:
            raise ValidationError("Workflow name is required")

        node_ids = {node.id for node in definition.nodes}
        start_nodes = [node for node in definition.nodes if node.type == "START"]
        end_nodes = [node for node in definition.nodes if node.type == "END"]

        if len(start_nodes) != 1:
            raise ValidationError("Workflow must contain exactly one START node")
        if len(end_nodes) != 1:
            raise ValidationError("Workflow must contain exactly one END node")

        for edge in definition.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValidationError("Workflow edges must reference existing nodes")

    def create_workflow(
        self, definition: WorkflowDefinition, tenant_id: TenantId
    ) -> WorkflowDefinition:
        self._validate_definition(definition)
        if definition.name in self._definitions:
            raise ConflictError("Workflow already exists")

        self._definitions[definition.name] = definition
        return definition

    def _snapshot_run(self, run: WorkflowRun) -> WorkflowRun:
        return run.model_copy(deep=True)

    def _execute_workflow_hook(
        self,
        event_type: HookEventType,
        payload: dict[str, object],
        tenant_id: TenantId,
    ) -> dict[str, object]:
        if self._hook_engine is None:
            return payload
        return self._hook_engine.execute_hooks(
            event_type=event_type,
            payload=payload,
            tenant_id=tenant_id,
        )

    def create_run(self, workflow_name: str, tenant_id: TenantId) -> WorkflowRun:
        if workflow_name not in self._definitions:
            raise ValidationError("Workflow not found")

        pre_payload = {"workflow_name": workflow_name, "tenant_id": tenant_id}
        if self._hook_engine is not None:
            pre_payload = self._hook_engine.execute_hooks(
                event_type=HookEventType.PRE_WORKFLOW_RUN,
                payload=pre_payload,
                tenant_id=tenant_id,
            )
            if pre_payload.get("hook_aborted"):
                run = WorkflowRun(
                    id=f"run-{len(self._runs) + 1}",
                    workflow_id=workflow_name,
                    tenant_id=tenant_id,
                    status="CANCELLED",
                    state=pre_payload,
                )
                self._runs[run.id] = run
                return self._snapshot_run(run)

        run = WorkflowRun(
            id=f"run-{len(self._runs) + 1}",
            workflow_id=workflow_name,
            tenant_id=tenant_id,
            status="RUNNING",
            state=pre_payload,
        )
        self._runs[run.id] = run

        if self._hook_engine is not None:
            post_payload = self._hook_engine.execute_hooks(
                event_type=HookEventType.POST_WORKFLOW_RUN,
                payload={
                    "workflow_name": workflow_name,
                    "run_id": run.id,
                    "status": run.status,
                },
                tenant_id=tenant_id,
            )
            if post_payload.get("hook_aborted"):
                run.status = "CANCELLED"
                run.state = post_payload
        return self._snapshot_run(run)

    def pause_run(self, run_id: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise ValidationError("Run not found")
        if run.status != "RUNNING":
            raise ConflictError("Run is not running")

        pre_payload = self._execute_workflow_hook(
            HookEventType.PRE_WORKFLOW_PAUSE,
            {"run_id": run.id, "workflow_id": run.workflow_id},
            run.tenant_id,
        )
        if pre_payload.get("hook_aborted"):
            run.state = pre_payload
            return self._snapshot_run(run)

        run.status = "PAUSED"
        run.state = pre_payload

        post_payload = self._execute_workflow_hook(
            HookEventType.POST_WORKFLOW_PAUSE,
            {"run_id": run.id, "workflow_id": run.workflow_id, "status": run.status},
            run.tenant_id,
        )
        if post_payload.get("hook_aborted"):
            run.state = post_payload
        return self._snapshot_run(run)

    def resume_run(self, run_id: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise ValidationError("Run not found")
        if run.status != "PAUSED":
            raise ConflictError("Run is not paused")

        pre_payload = self._execute_workflow_hook(
            HookEventType.PRE_WORKFLOW_RESUME,
            {"run_id": run.id, "workflow_id": run.workflow_id},
            run.tenant_id,
        )
        if pre_payload.get("hook_aborted"):
            run.state = pre_payload
            return self._snapshot_run(run)

        run.status = "RUNNING"
        run.state = pre_payload

        post_payload = self._execute_workflow_hook(
            HookEventType.POST_WORKFLOW_RESUME,
            {"run_id": run.id, "workflow_id": run.workflow_id, "status": run.status},
            run.tenant_id,
        )
        if post_payload.get("hook_aborted"):
            run.state = post_payload
        return self._snapshot_run(run)

    def cancel_run(self, run_id: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise ValidationError("Run not found")
        if run.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise ConflictError("Run is already in a terminal state")

        pre_payload = self._execute_workflow_hook(
            HookEventType.PRE_WORKFLOW_CANCEL,
            {"run_id": run.id, "workflow_id": run.workflow_id},
            run.tenant_id,
        )
        if pre_payload.get("hook_aborted"):
            run.state = pre_payload
            return self._snapshot_run(run)

        run.status = "CANCELLED"
        run.state = pre_payload

        post_payload = self._execute_workflow_hook(
            HookEventType.POST_WORKFLOW_CANCEL,
            {"run_id": run.id, "workflow_id": run.workflow_id, "status": run.status},
            run.tenant_id,
        )
        if post_payload.get("hook_aborted"):
            run.state = post_payload
        return self._snapshot_run(run)

    def list_runs(self, tenant_id: TenantId) -> list[WorkflowRun]:
        return list(self._runs.values())

    def execute_run_sync(self, run_id: str) -> ExecutionResult:
        """Execute the workflow run synchronously to completion using the injected runtime.

        This method keeps WorkflowService decoupled from the runtime implementation
        by depending only on `WorkflowRuntime` abstraction.
        """
        run = self._runs.get(run_id)
        if run is None:
            raise ValidationError("Run not found")
        if self._workflow_runtime is None:
            raise ValidationError("No workflow runtime available")

        definition = self._definitions.get(run.workflow_id)
        if definition is None:
            raise ValidationError("Workflow not found")

        graph_id = run.id
        # compile graph
        self._workflow_runtime.compile_graph(graph_id=graph_id, definition=definition.model_dump())
        # execute synchronously
        result = self._workflow_runtime.execute(graph_id=graph_id)

        # Update run status based on result
        run.state = {"last_result": result}
        run.status = "COMPLETED" if result.status == "COMPLETED" else "FAILED"
        self._runs[run.id] = run
        return result

    async def stream_run(self, run_id: str) -> AsyncGenerator[ExecutionChunk]:
        """Return an async generator streaming execution chunks from the runtime."""
        run = self._runs.get(run_id)
        if run is None:
            raise ValidationError("Run not found")
        if self._workflow_runtime is None:
            raise ValidationError("No workflow runtime available")

        definition = self._definitions.get(run.workflow_id)
        if definition is None:
            raise ValidationError("Workflow not found")

        graph_id = run.id
        self._workflow_runtime.compile_graph(graph_id=graph_id, definition=definition.model_dump())
        async for chunk in self._workflow_runtime.astream(graph_id=graph_id):
            yield chunk
