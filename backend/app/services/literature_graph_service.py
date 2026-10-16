from collections import Counter,deque
from pathlib import Path
import json
from app.schemas.graph import GraphData,GraphNode,GraphEdge,GraphMeta,GraphResponse

class LiteratureGraphService:
    def __init__(self):
        self.path=Path(__file__).resolve().parents[2]/'data/literature_graph.json'
    def _raw(self):return json.loads(self.path.read_text(encoding='utf-8'))
    def _response(self,raw,nodes,edges):
        return GraphResponse(data=GraphData(nodes=[GraphNode(**n) for n in nodes],edges=[GraphEdge(**e) for e in edges]),meta=GraphMeta(total_nodes=len(nodes),total_edges=len(edges),node_type_stats=dict(Counter(n['type'] for n in nodes)),edge_type_stats=dict(Counter(e['type'] for e in edges)),version=raw['meta']['version'],as_of=raw['meta']['as_of'],evidence_edges=sum(e['evidence_status']!='hypothesis' for e in edges),hypothesis_edges=sum(e['evidence_status']=='hypothesis' for e in edges)),sources=raw['sources'])
    def get_all(self):
        raw=self._raw();return self._response(raw,raw['nodes'],raw['edges'])
    def search(self,keyword,depth=2,include_hypotheses=False):
        raw=self._raw();keyword=keyword.strip().casefold()
        if not keyword:return self._response(raw,raw['nodes'],raw['edges'])
        matched={n['id'] for n in raw['nodes'] if keyword in n['name'].casefold() or any(keyword==str(a).casefold() for a in n['properties'].get('aliases',[])) or keyword==str(n['properties'].get('pubchem_cid',''))}
        for e in raw['edges']:
            if keyword in [r.casefold() for r in e.get('source_ids',[])]:matched.update([e['source'],e['target']])
        adjacency={n['id']:set() for n in raw['nodes']}
        for e in raw['edges']:
            if e['evidence_status']=='hypothesis' and not include_hypotheses:continue
            adjacency[e['source']].add(e['target']);adjacency[e['target']].add(e['source'])
        seen=set(matched);queue=deque((n,0) for n in sorted(matched))
        while queue:
            n,d=queue.popleft()
            if d>=depth:continue
            for other in adjacency[n]:
                if other not in seen:seen.add(other);queue.append((other,d+1))
        return self._response(raw,[n for n in raw['nodes'] if n['id'] in seen],[e for e in raw['edges'] if e['source'] in seen and e['target'] in seen and (include_hypotheses or e['evidence_status']!='hypothesis')])
    def neighbors(self,node_id):
        raw=self._raw();edges=[e for e in raw['edges'] if node_id in [e['source'],e['target']]]
        ids={node_id}|{e[x] for e in edges for x in ['source','target']}
        return self._response(raw,[n for n in raw['nodes'] if n['id'] in ids],edges)
