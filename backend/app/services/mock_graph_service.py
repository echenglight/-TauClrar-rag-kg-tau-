from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.schemas.graph import GraphData, GraphEdge, GraphMeta, GraphNode, GraphResponse


class MockGraphService:
    """Mock 图谱读取与查询服务。"""

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        self.mock_path = root / settings.mock_data_file

    def _load_raw(self) -> dict:
        with self.mock_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_all(self) -> GraphResponse:
        raw = self._load_raw()
        nodes = [GraphNode(**node) for node in raw.get("nodes", [])]
        edges = [GraphEdge(**edge) for edge in raw.get("edges", [])]
        meta = self._build_meta(nodes, edges)
        return GraphResponse(data=GraphData(nodes=nodes, edges=edges), meta=meta)

    def search(self, keyword: str) -> GraphResponse:
        keyword = keyword.strip().lower()
        all_data = self.get_all()
        if not keyword:
            return all_data

        matched_nodes = [
            node
            for node in all_data.data.nodes
            if keyword in node.name.lower()
            or keyword in node.type.lower()
            or keyword in str(node.properties).lower()
        ]
        matched_ids = {n.id for n in matched_nodes}
        matched_edges = [
            edge
            for edge in all_data.data.edges
            if edge.source in matched_ids or edge.target in matched_ids
        ]

        # 保证边关联的节点完整。
        for edge in matched_edges:
            matched_ids.add(edge.source)
            matched_ids.add(edge.target)

        final_nodes = [node for node in all_data.data.nodes if node.id in matched_ids]
        meta = self._build_meta(final_nodes, matched_edges)
        return GraphResponse(data=GraphData(nodes=final_nodes, edges=matched_edges), meta=meta)

    def _build_meta(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphMeta:
        node_type_stats: dict[str, int] = {}
        edge_type_stats: dict[str, int] = {}

        for n in nodes:
            node_type_stats[n.type] = node_type_stats.get(n.type, 0) + 1
        for e in edges:
            edge_type_stats[e.type] = edge_type_stats.get(e.type, 0) + 1

        return GraphMeta(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_type_stats=node_type_stats,
            edge_type_stats=edge_type_stats,
        )
