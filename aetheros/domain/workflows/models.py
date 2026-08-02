from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from aetheros.domain.shared.value_objects import TenantId


class WorkflowNode(BaseModel):
    id: str
    type: str
    agent_id: str | None = None
    condition: str | None = None


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    name: str
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_structure(self) -> WorkflowDefinition:
        if not self.nodes:
            raise ValueError("Workflow must contain at least one node")
        if not any(node.type == "START" for node in self.nodes):
            raise ValueError("Workflow must contain a START node")
        if not any(node.type == "END" for node in self.nodes):
            raise ValueError("Workflow must contain an END node")

        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError("Workflow edges must reference existing nodes")
        return self


class WorkflowRun(BaseModel):
    id: str
    workflow_id: str
    tenant_id: TenantId
    status: str = "PENDING"
    state: dict[str, object] = Field(default_factory=dict)
    output_data: dict[str, object] | None = None
