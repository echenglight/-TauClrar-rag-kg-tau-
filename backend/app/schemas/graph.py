from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    size: int = 50
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    weight: float = 0.5
    evidence: str | None = None


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphMeta(BaseModel):
    total_nodes: int
    total_edges: int
    node_type_stats: dict[str, int]
    edge_type_stats: dict[str, int]


class GraphResponse(BaseModel):
    data: GraphData
    meta: GraphMeta
