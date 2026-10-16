from fastapi import APIRouter,Query,HTTPException
from app.services.literature_graph_service import LiteratureGraphService
from app.services.evidence_rank_service import LightGNNService
from app.services.molecule_feature_service import MoleculeFeatureService
from app.schemas.analysis import IntegratedSearchResponse

graph_router=APIRouter(prefix='/api/graph',tags=['literature-graph'])
analysis_router=APIRouter(prefix='/api/analysis',tags=['analysis'])
graph_service=LiteratureGraphService();gnn_service=LightGNNService();molecule_service=MoleculeFeatureService()

@graph_router.get('/all')
def all_graph(limit:int=Query(500,ge=1,le=3000)):
    # Curated graph is smaller than the request cap. Do not silently truncate edges.
    return graph_service.get_all()

@graph_router.get('/search')
def search(keyword:str=''):return graph_service.search(keyword)

@graph_router.get('/neighbors/{node_id}')
def neighbors(node_id:str):
    result=graph_service.neighbors(node_id)
    if not result.data.nodes:raise HTTPException(404,'节点不存在')
    return result

@graph_router.get('/sources')
def sources():return graph_service.get_all().sources

@analysis_router.get('/search',response_model=IntegratedSearchResponse)
def integrated_search(keyword:str='',graph_limit:int=Query(400,ge=1,le=3000),molecule_limit:int=Query(5,ge=1,le=20),gnn_top_k:int=Query(20,ge=1,le=100),include_hypotheses:bool=False):
    keyword=keyword.strip();full=graph_service.get_all();kg=graph_service.search(keyword,depth=4,include_hypotheses=include_hypotheses)
    profiles=molecule_service.search(keyword,molecule_limit)
    result=gnn_service.infer(full.data.nodes,full.data.edges,profiles,keyword,gnn_top_k,include_hypotheses)
    notes=['有向证据路径排序；分数不是准确率、效应大小或概率。']
    if keyword and not kg.data.nodes:notes.append('未检索到匹配实体。')
    if profiles and keyword and not result.predictions:notes.append('身份已匹配；当前文献证据层无可追溯机制候选。待验证关系可单独查看。')
    return IntegratedSearchResponse(keyword=keyword,kg=kg,molecules=profiles,gnn=result,notes=notes)
