from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.graph import GraphData, GraphEdge, GraphMeta, GraphNode, GraphResponse
from app.schemas.template import (
    TemplateDetailResponse,
    TemplateListResponse,
    TemplateSummary,
)


class TemplateGraphService:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        self.template_path = root / settings.template_graph_file

    def list_templates(self) -> TemplateListResponse:
        raw = self._load_raw()
        templates = [
            TemplateSummary(
                id=item.get("id", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
            )
            for item in raw.get("templates", [])
        ]
        return TemplateListResponse(templates=templates)

    def get_template(self, template_id: str) -> TemplateDetailResponse:
        raw = self._load_raw()
        for item in raw.get("templates", []):
            if item.get("id") != template_id:
                continue

            nodes = [GraphNode(**node) for node in item.get("nodes", [])]
            edges = [GraphEdge(**edge) for edge in item.get("edges", [])]

            return TemplateDetailResponse(
                id=template_id,
                title=item.get("title", template_id),
                description=item.get("description", ""),
                relation_legend=item.get("relation_legend", {}),
                graph=GraphResponse(
                    data=GraphData(nodes=nodes, edges=edges),
                    meta=self._build_meta(nodes, edges),
                ),
            )

        raise HTTPException(status_code=404, detail="模板不存在")

    def _load_raw(self) -> dict:
        if not self.template_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"模板文件不存在: {self.template_path}",
            )

        with self.template_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _build_meta(nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphMeta:
        node_type_stats: dict[str, int] = {}
        edge_type_stats: dict[str, int] = {}

        for node in nodes:
            node_type_stats[node.type] = node_type_stats.get(node.type, 0) + 1
        for edge in edges:
            edge_type_stats[edge.type] = edge_type_stats.get(edge.type, 0) + 1

        return GraphMeta(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_type_stats=node_type_stats,
            edge_type_stats=edge_type_stats,
        )
