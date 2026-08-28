import asyncio

from aetheros.application.langgraph.runtime_api import (
    ExecutionChunk,
    ExecutionResult,
    WorkflowRuntime,
)
from aetheros.application.workflows.workflow_service import WorkflowService
from aetheros.domain.shared.value_objects import TenantId
from aetheros.domain.workflows.models import (
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)


class MockRuntime(WorkflowRuntime):
    def __init__(self):
        self.compiled = {}

    def compile_graph(self, graph_id: str, definition: dict) -> dict:
        self.compiled[graph_id] = definition
        return {"id": graph_id, "definition": definition, "position": 0}

    def execute(self, graph_id: str, config: dict | None = None) -> ExecutionResult:
        outputs = [{"text": "ok-1"}, {"text": "ok-2"}]
        return ExecutionResult(
            graph_id=graph_id, status="COMPLETED", outputs=outputs
        )

    async def astream(self, graph_id: str, config: dict | None = None):
        yield ExecutionChunk(graph_id=graph_id, event="start", position=0)
        yield ExecutionChunk(
            graph_id=graph_id,
            event="node",
            node_index=0,
            output={"text": "chunk-0"},
        )
        yield ExecutionChunk(graph_id=graph_id, event="complete", position=1)

    def interrupt(self, graph_id: str) -> None:
        pass

    def resume(self, graph_id: str) -> None:
        pass

    async def checkpoint(self, graph_id: str) -> dict:
        return {"id": graph_id}


def make_definition() -> WorkflowDefinition:
    nodes = [
        WorkflowNode(id="start", type="START"),
        WorkflowNode(id="end", type="END"),
    ]
    edges = [WorkflowEdge(id="e1", source="start", target="end")]
    return WorkflowDefinition(name="test", nodes=nodes, edges=edges)


def test_workflow_service_execute_with_mock_runtime():
    runtime = MockRuntime()
    service = WorkflowService(hook_engine=None, workflow_runtime=runtime)

    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("t1"))

    run = service.create_run(
        workflow_name=definition.name, tenant_id=TenantId("t1")
    )
    # execute synchronously
    result = service.execute_run_sync(run.id)
    assert result.graph_id == run.id
    assert result.status == "COMPLETED"
    # ensure run status updated
    updated = service.list_runs(tenant_id=TenantId("t1"))[0]
    assert updated.status == "COMPLETED"


def test_workflow_service_stream_with_mock_runtime():
    runtime = MockRuntime()
    service = WorkflowService(hook_engine=None, workflow_runtime=runtime)

    definition = make_definition()
    service.create_workflow(definition=definition, tenant_id=TenantId("t1"))
    run = service.create_run(
        workflow_name=definition.name, tenant_id=TenantId("t1")
    )

    async def collect_stream():
        chunks = []
        async for chunk in service.stream_run(run.id):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(collect_stream())
    assert any(c.event == "start" for c in chunks)
    assert any(c.event == "complete" for c in chunks)
