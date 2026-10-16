from collections import defaultdict
from app.schemas.analysis import GNNPrediction,GNNResult

class LightGNNService:
    """Directed evidence-path ranking. Fixed weights, not trained GNN probabilities."""
    TARGET_TYPES={'Protein','Pathway','Phenotype'}
    def infer(self,nodes,edges,molecules,keyword,top_k=5,include_hypotheses=False):
        key=keyword.strip().casefold()
        if not key:return GNNResult(model_name='EvidenceGraphRank-v2',top_k=top_k,predictions=[])
        seeds={n.id for n in nodes if n.type=='Compound' and (key==str(n.properties.get('pubchem_cid','')).casefold() or key==n.name.casefold() or key in [str(a).casefold() for a in n.properties.get('aliases',[])])}
        node_map={n.id:n for n in nodes};adj=defaultdict(list)
        for edge in edges:
            if edge.evidence_status=='hypothesis' and not include_hypotheses:continue
            if edge.weight<=0:continue
            adj[edge.source].append(edge)
        for k in adj:adj[k].sort(key=lambda e:e.id)
        best={}
        def walk(current,node_path,edge_path,product):
            if edge_path:
                score=round(product*(.82**(len(edge_path)-1)),4)
                tie=(tuple(e.id for e in edge_path),tuple(node_path))
                old=best.get(current)
                if old is None or score>old[0] or (score==old[0] and (len(edge_path),tie)<(len(old[2]),old[3])):best[current]=(score,list(node_path),list(edge_path),tie)
            if len(edge_path)>=4:return
            for edge in adj[current]:
                if edge.target in node_path or (node_map[edge.target].type=='Compound' and edge.target not in seeds):continue
                walk(edge.target,node_path+[edge.target],edge_path+[edge],product*edge.weight)
        for seed in sorted(seeds):walk(seed,[seed],[],1.)
        predictions=[]
        for target,(score,path,chain,_) in best.items():
            node=node_map[target]
            if node.type not in self.TARGET_TYPES:continue
            hypothesis=any(e.evidence_status=='hypothesis' for e in chain)
            state='hypothesis' if hypothesis else 'direct_literature' if len(chain)==1 and chain[0].evidence_status=='experimental' else 'cross_study_inference'
            predictions.append(GNNPrediction(node_id=node.id,node_name=node.name,node_type=node.type,score=score,hops=len(chain),path_node_ids=path,path_edge_ids=[e.id for e in chain],source_ids=sorted({s for e in chain for s in e.source_ids}),evidence_status=state,explanation=f'{len(chain)} 跳有向证据路径；'+ ' → '.join(node_map[p].name for p in path)))
        predictions.sort(key=lambda p:(-p.score,p.hops,p.node_name,p.node_id))
        return GNNResult(model_name='EvidenceGraphRank-v2',top_k=top_k,predictions=predictions[:top_k])
