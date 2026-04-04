from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase

from app.core.config import settings
from app.schemas.graph import GraphData, GraphEdge, GraphMeta, GraphNode, GraphResponse


class Neo4jGraphService:
    """Neo4j 图谱查询服务。"""

    def __init__(self) -> None:
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self) -> None:
        self.driver.close()

    def get_all(self, limit: int = 500) -> GraphResponse:
        with self.driver.session() as session:
            rows = session.run(
                """
                MATCH (a)-[r]->(b)
                RETURN a, r, b
                LIMIT $limit
                """,
                limit=limit,
            )
            return self._to_graph_response(rows.data())

    def search(self, keyword: str, limit: int = 300) -> GraphResponse:
        with self.driver.session() as session:
            rows = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE toLower(coalesce(a.name, '')) CONTAINS toLower($keyword)
                   OR toLower(coalesce(b.name, '')) CONTAINS toLower($keyword)
                RETURN a, r, b
                LIMIT $limit
                """,
                keyword=keyword,
                limit=limit,
            )
            return self._to_graph_response(rows.data())

    def _to_graph_response(self, rows: list[dict[str, Any]]) -> GraphResponse:
        node_map: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        for row in rows:
            a = row["a"]
            b = row["b"]
            r = row["r"]

            a_id = str(a.get("id", a.element_id))
            b_id = str(b.get("id", b.element_id))

            if a_id not in node_map:
                a_type = list(a.labels)[0] if a.labels else "Entity"
                node_map[a_id] = GraphNode(
                    id=a_id,
                    name=a.get("name", a_id),
                    type=a_type,
                    size=int(a.get("size", 50)),
                    properties=dict(a),
                )

            if b_id not in node_map:
                b_type = list(b.labels)[0] if b.labels else "Entity"
                node_map[b_id] = GraphNode(
                    id=b_id,
                    name=b.get("name", b_id),
                    type=b_type,
                    size=int(b.get("size", 50)),
                    properties=dict(b),
                )

            edge_type = r.type
            edge = GraphEdge(
                id=str(r.element_id),
                source=a_id,
                target=b_id,
                type=edge_type,
                weight=float(r.get("weight", 0.5)),
                evidence=r.get("evidence"),
            )
            edges.append(edge)

        nodes = list(node_map.values())
        node_type_stats: dict[str, int] = {}
        edge_type_stats: dict[str, int] = {}

        for n in nodes:
            node_type_stats[n.type] = node_type_stats.get(n.type, 0) + 1
        for e in edges:
            edge_type_stats[e.type] = edge_type_stats.get(e.type, 0) + 1

        return GraphResponse(
            data=GraphData(nodes=nodes, edges=edges),
            meta=GraphMeta(
                total_nodes=len(nodes),
                total_edges=len(edges),
                node_type_stats=node_type_stats,
                edge_type_stats=edge_type_stats,
            ),
        )
