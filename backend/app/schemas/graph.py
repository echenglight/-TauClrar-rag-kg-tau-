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
    label: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    evidence_status: str = "annotation"
    context: str = ""
    origin: str | None = None


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphMeta(BaseModel):
    total_nodes: int
    total_edges: int
    node_type_stats: dict[str, int]
    edge_type_stats: dict[str, int]
    version: str = "2.0.0"
    as_of: str = "2026-10-16"
    evidence_edges: int = 0
    hypothesis_edges: int = 0


class GraphResponse(BaseModel):
    data: GraphData
    meta: GraphMeta
    sources: dict[str, Any] = Field(default_factory=dict)
