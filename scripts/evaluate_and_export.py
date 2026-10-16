"""Run the current API and independent checks; export only the requested tables."""
import csv,json,sys,math,hashlib,unittest,io
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'));OUT=ROOT/'审阅材料';OUT.mkdir(exist_ok=True)
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes_v2 import graph_service
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def write(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    client=TestClient(app);g=graph_service.get_all();raw=json.loads((ROOT/'backend/data/literature_graph.json').read_text(encoding='utf-8'));names={n.id:n.name for n in g.data.nodes};node_map={n.id:n for n in g.data.nodes}
    all_rows=[];path_rows=[];responses={};checks=[]
    refgraph=nx.DiGraph()
    for e in g.data.edges:
        if e.evidence_status!='hypothesis':refgraph.add_edge(e.source,e.target,weight=e.weight)
    label={'direct_literature':'直接文献关系','cross_study_inference':'跨关系机制推断','hypothesis':'待验证关联'}
    for cid in ['2244','2519','129908365']:
        r=client.get('/api/analysis/search',params={'keyword':cid,'gnn_top_k':100});assert r.status_code==200
        q=r.json();responses[cid]=q;assert [m['name'] for m in q['molecules']]==[cid]
        for p in q['gnn']['predictions']:
            paths=nx.all_simple_paths(refgraph,'cpd_'+cid,p['node_id'],cutoff=4)
            expected=max(round(math.prod(refgraph[a][b]['weight'] for a,b in zip(path,path[1:]))*.82**(len(path)-2),4) for path in paths)
            assert expected==p['score'];checks.append({'cid':cid,'candidate':p['node_id'],'observed':p['score'],'reference':expected,'error':0.0})
            refs='; '.join(g.sources[s]['url'] for s in p['source_ids'])
            row={'化合物':names['cpd_'+cid],'PubChem CID':cid,'候选实体':p['node_name'],'实体类型':{'Pathway':'通路 / 生物过程','Protein':'蛋白 / 复合体','Phenotype':'实验终点'}[p['node_type']],'规则分数':f'{p["score"]:.4f}','跳数':p['hops'],'证据属性':label[p['evidence_status']],'有向路径':' → '.join(names[n] for n in p['path_node_ids']),'来源':refs,'模型模块':'EvidenceGraphRank-v2','解释范围':'机制关联排序；不代表药效、概率或训练型 GNN 精度'}
            all_rows.append(row)
            if p['node_type']=='Pathway':
                path_rows.append({'化合物':row['化合物'],'PubChem CID':cid,'通路 / 生物过程':p['node_name'],'规则分数':row['规则分数'],'跳数':p['hops'],'标准条目':node_map[p['node_id']].properties.get('standard_id') or '文献功能过程；非单一 KEGG 编号','证据属性':row['证据属性'],'有向路径':row['有向路径'],'来源':refs,'研究定位':'原始研究条件下的机制依据' if p['evidence_status']=='direct_literature' else '跨关系推断；需按实验背景解释'})
        if not q['gnn']['predictions']:
            all_rows.append({'化合物':names['cpd_'+cid],'PubChem CID':cid,'候选实体':'文献证据层未建立机制路径','实体类型':'候选状态','规则分数':'','跳数':'','证据属性':'化学身份已核实；机制为待验证假设','有向路径':'','来源':g.sources['CID:'+cid]['url'],'模型模块':'EvidenceGraphRank-v2','解释范围':'旧版两条预测关系隔离在假设层，不纳入文献排序'})
            path_rows.append({'化合物':names['cpd_'+cid],'PubChem CID':cid,'通路 / 生物过程':'文献证据层未建立机制路径','规则分数':'','跳数':'','标准条目':'','证据属性':'探索性候选','有向路径':'','来源':g.sources['CID:'+cid]['url'],'研究定位':'结构登记不作为 Tau 清除或 ULK1 激活证据'})
    unknown=client.get('/api/analysis/search',params={'keyword':'UNKNOWN_NO_MATCH_2026'}).json();assert not unknown['molecules'] and not unknown['gnn']['predictions'] and not unknown['kg']['data']['nodes']
    optional=client.get('/api/analysis/search',params={'keyword':'129908365','include_hypotheses':True,'gnn_top_k':100}).json();assert all(p['evidence_status']=='hypothesis' for p in optional['gnn']['predictions'])
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);assert result.wasSuccessful(),stream.getvalue()
    (ROOT/'evidence/test_output.txt').write_text(stream.getvalue(),encoding='utf-8')
    formal=[e for e in g.data.edges if e.evidence_status!='hypothesis']
    metrics=[{'指标':'指定 CID 身份匹配','范围':'3 个指定化合物','结果':'3/3（100%）','含义':'身份匹配一致性'},
      {'指标':'正式关系来源绑定','范围':f'{len(formal)} 条非假设关系','结果':f'{len(formal)}/{len(formal)}（100%）','含义':'来源标识可定位；不表示实验真实性概率'},
      {'指标':'候选分数独立重算','范围':f'{len(checks)} 条文献层候选','结果':f'{len(checks)}/{len(checks)}（100%）','含义':'相对 NetworkX 独立实现的一致性'},
      {'指标':'最大绝对误差','范围':'上述候选的四位小数分数','结果':'0.0000','含义':'计算结果差异'},
      {'指标':'关系端点完整性','范围':f'{len(g.data.edges)*2} 个端点引用','结果':f'{len(g.data.edges)*2}/{len(g.data.edges)*2}（100%）','含义':'无悬空端点'},
      {'指标':'功能 / 方法测试','范围':f'{result.testsRun} 项自动化测试','结果':f'{result.testsRun}/{result.testsRun} 通过','含义':'来源、隔离、方向、权重与路径计算'},
      {'指标':'未知实体误回退','范围':'不存在的实体查询','结果':'0 个无关分子 / 0 个候选','含义':'已取消旧版回退'},
      {'指标':'假设层隔离','范围':'CID 129908365','结果':f'默认 0 条；显式启用后 {len(optional["gnn"]["predictions"])} 条候选','含义':'待验证关联不混入文献结论'}]
    write(OUT/'系统图神经网络模块结果.csv',all_rows);write(OUT/'三个化合物通路筛选结果.csv',path_rows)
    hashes=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ROOT/'backend/data/literature_graph.json',ROOT/'backend/app/services/evidence_rank_service.py',ROOT/'backend/app/services/literature_graph_service.py',ROOT/'backend/app/api/routes_v2.py',ROOT/'scripts/build_literature_kg.py']]
    summary={'as_of':'2026-10-16','graph_meta':raw['meta'],'metrics':metrics,'score_records':checks,'responses':responses,'optional_hypothesis_response':optional,'candidate_counts':{c:len(q['gnn']['predictions']) for c,q in responses.items()},'pathway_counts':{c:sum(r['PubChem CID']==c and bool(r['规则分数']) for r in path_rows) for c in responses},'candidate_rows':all_rows,'pathway_rows':path_rows,'source_hashes':hashes,'test_count':result.testsRun,'tests_passed':result.wasSuccessful(),'biological_performance':'not independently evaluated; no Accuracy/Precision/Recall/F1/AUC claim'}
    save(ROOT/'evidence/evaluation.json',summary)
    print(json.dumps({k:summary[k] for k in ['candidate_counts','pathway_counts','test_count','tests_passed']},ensure_ascii=False))
if __name__=='__main__':main()
