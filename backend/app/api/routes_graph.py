from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.schemas.graph import GraphData, GraphMeta, GraphResponse
from app.services.mock_graph_service import MockGraphService

router = APIRouter(prefix="/api/graph", tags=["graph"])

mock_service = MockGraphService()


def _is_neo4j_mode() -> bool:
    return settings.graph_source.lower() == "neo4j"


def _get_neo4j_service():
    # 懒加载：仅在 neo4j 模式下导入，避免 mock 模式被可选依赖拖垮。
    from app.services.neo4j_service import Neo4jGraphService

    return Neo4jGraphService()


@router.get("/all")
def get_graph_all(limit: int = Query(default=500, ge=1, le=3000)) -> GraphResponse:
    """获取图谱全量数据。"""
    if _is_neo4j_mode():
        service = _get_neo4j_service()
        try:
            return service.get_all(limit=limit)
        finally:
            service.close()
    return mock_service.get_all()


@router.get("/search")
def search_graph(
    keyword: str = Query(default="", description="按名称或属性搜索"),
    limit: int = Query(default=300, ge=1, le=3000),
) -> GraphResponse:
    """按关键字搜索图谱。"""
    if _is_neo4j_mode():
        service = _get_neo4j_service()
        try:
            return service.search(keyword=keyword, limit=limit)
        finally:
            service.close()
    return mock_service.search(keyword=keyword)


@router.get("/neighbors/{node_id}")
def get_neighbors(node_id: str) -> GraphResponse:
    """返回节点一阶邻居子图（基于当前数据源）。"""
    if _is_neo4j_mode():
        service = _get_neo4j_service()
        try:
            graph = service.get_all(limit=1200)
        finally:
            service.close()
    else:
        graph = mock_service.get_all()

    hit = [n for n in graph.data.nodes if n.id == node_id]
    if not hit:
        raise HTTPException(status_code=404, detail="节点不存在")

    edges = [
        e
        for e in graph.data.edges
        if e.source == node_id or e.target == node_id
    ]
    related_ids = {node_id}
    for e in edges:
        related_ids.add(e.source)
        related_ids.add(e.target)
    nodes = [n for n in graph.data.nodes if n.id in related_ids]

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
