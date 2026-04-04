from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.routes_graph import _get_neo4j_service, _is_neo4j_mode, mock_service
from app.schemas.analysis import IntegratedSearchResponse
from app.services.gnn_service import LightGNNService
from app.services.molecule_feature_service import MoleculeFeatureService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

molecule_service = MoleculeFeatureService()
gnn_service = LightGNNService()


@router.get("/search", response_model=IntegratedSearchResponse)
def integrated_search(
    keyword: str = Query(default="", description="统一检索关键词"),
    graph_limit: int = Query(default=300, ge=1, le=3000),
    molecule_limit: int = Query(default=5, ge=1, le=20),
    gnn_top_k: int = Query(default=5, ge=1, le=20),
) -> IntegratedSearchResponse:
    """返回 KG + 分子指纹 + GNN 推理结果。"""
    normalized = keyword.strip()
    fallback_to_full_graph = False

    if _is_neo4j_mode():
        service = _get_neo4j_service()
        try:
            kg = service.search(keyword=normalized, limit=graph_limit)
            if normalized and kg.meta.total_nodes == 0:
                kg = service.get_all(limit=graph_limit)
                fallback_to_full_graph = True
        finally:
            service.close()
    else:
        kg = mock_service.search(normalized)
        if normalized and kg.meta.total_nodes == 0:
            kg = mock_service.get_all()
            fallback_to_full_graph = True

    molecules = molecule_service.search(normalized, limit=molecule_limit)
    gnn = gnn_service.infer(
        nodes=kg.data.nodes,
        edges=kg.data.edges,
        molecules=molecules,
        keyword=normalized,
        top_k=gnn_top_k,
    )

    notes = list(molecule_service.last_notes)
    if fallback_to_full_graph:
        notes.append("关键词未命中图谱实体，已回退到全量 KG 用于联动展示。")
    if not gnn.predictions:
        notes.append("GNN 未生成候选，可能是当前子图中缺少 Compound 节点。")

    return IntegratedSearchResponse(
        keyword=normalized,
        kg=kg,
        molecules=molecules,
        gnn=gnn,
        notes=notes,
    )
