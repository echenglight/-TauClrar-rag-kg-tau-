import sys,unittest,json,math
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes_v2 import graph_service,gnn_service,molecule_service
import networkx as nx

class LiteratureKGTest(unittest.TestCase):
    def setUp(self):self.client=TestClient(app);self.g=graph_service.get_all()
    def query(self,cid,**extra):return self.client.get('/api/analysis/search',params={'keyword':cid,'gnn_top_k':100,**extra}).json()
    def test_source_integrity(self):
        ids=[n.id for n in self.g.data.nodes];self.assertEqual(len(ids),len(set(ids)))
        edgeids=[e.id for e in self.g.data.edges];self.assertEqual(len(edgeids),len(set(edgeids)))
        for e in self.g.data.edges:
            self.assertIn(e.source,ids);self.assertIn(e.target,ids)
            if e.evidence_status!='hypothesis':
                self.assertTrue(e.source_ids)
                for ref in e.source_ids:self.assertIn(ref,self.g.sources)
        self.assertEqual(sum(e.evidence_status=='hypothesis' for e in self.g.data.edges),2)
    def test_known_and_unknown_entities(self):
        for cid in ['2244','2519','129908365']:
            q=self.query(cid);self.assertEqual([m['name'] for m in q['molecules']],[cid])
        q=self.query('UNKNOWN_NO_MATCH_2026');self.assertEqual(q['molecules'],[]);self.assertEqual(q['gnn']['predictions'],[]);self.assertEqual(q['kg']['data']['nodes'],[])
    def test_hypothesis_isolation(self):
        q=self.query('129908365')
        self.assertEqual(q['gnn']['predictions'],[])
        self.assertEqual(len(q['kg']['data']['nodes']),1)
        self.assertEqual(q['kg']['data']['edges'],[])
        p=self.query('129908365',include_hypotheses=True)['gnn']['predictions']
        self.assertGreater(len(p),0);self.assertTrue(all(x['evidence_status']=='hypothesis' for x in p))
    def test_independent_path_reference(self):
        G=nx.DiGraph()
        for e in self.g.data.edges:
            if e.evidence_status!='hypothesis':G.add_edge(e.source,e.target,weight=e.weight,edge_id=e.id)
        for cid in ['2244','2519']:
            predictions=self.query(cid)['gnn']['predictions'];first=self.query(cid)
            self.assertEqual(first,self.query(cid))
            for p in predictions:
                paths=list(nx.all_simple_paths(G,'cpd_'+cid,p['node_id'],cutoff=4))
                expected=max(round(math.prod(G[a][b]['weight'] for a,b in zip(path,path[1:]))*(.82**(len(path)-2)),4) for path in paths)
                self.assertAlmostEqual(p['score'],expected,places=8)
                self.assertLessEqual(p['hops'],4)
                for edge_id,a,b in zip(p['path_edge_ids'],p['path_node_ids'],p['path_node_ids'][1:]):self.assertEqual(G[a][b]['edge_id'],edge_id)
    def test_direction_and_weight_are_effective(self):
        q=self.query('2244')['gnn']['predictions'];self.assertTrue(q)
        reversed_edges=[e.model_copy(update={'source':e.target,'target':e.source}) for e in self.g.data.edges]
        reversed_result=gnn_service.infer(self.g.data.nodes,reversed_edges,[],'2244',100)
        self.assertEqual(reversed_result.predictions,[])
        zero=[e.model_copy(update={'weight':0.}) for e in self.g.data.edges]
        self.assertEqual(gnn_service.infer(self.g.data.nodes,zero,[],'2244',100).predictions,[])
    def test_pathway_labels_and_static_entry(self):
        for n in self.g.data.nodes:
            if n.type=='Pathway' and n.properties.get('standard_id'):self.assertIn(n.properties['standard_id'],self.g.sources)
        if (ROOT/'frontend/dist/index.html').exists():self.assertEqual(self.client.get('/').status_code,200)

if __name__=='__main__':unittest.main(verbosity=2)
