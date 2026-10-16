import {useState,useEffect,useMemo,useCallback} from 'react';
import {Search,Network,ArrowUpRight,BookOpen,Check,ChevronRight,Layers} from 'lucide-react';
import {EvidenceGraph,COLORS,LABELS} from './components/EvidenceGraph';
import type {GraphResponse,GraphEdge,IntegratedSearchResponse} from './types/graph';
const compoundChoices=[['','完整证据网络'],['2244','阿司匹林'],['2519','咖啡因'],['129908365','CID 129908365']];
export default function LiteratureApp(){
 const [all,setAll]=useState<GraphResponse|null>(null),[analysis,setAnalysis]=useState<IntegratedSearchResponse|null>(null),[query,setQuery]=useState(''),[active,setActive]=useState(''),[selected,setSelected]=useState<string|null>(null),[edge,setEdge]=useState<GraphEdge|null>(null),[hypotheses,setHypotheses]=useState(false),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const [types,setTypes]=useState<string[]>(Object.keys(LABELS));
 const apiBase=import.meta.env.VITE_API_BASE_URL?.trim()??'';
 useEffect(()=>{fetch(apiBase+'/api/graph/all').then(r=>{if(!r.ok)throw Error('无法读取图谱');return r.json()}).then(setAll).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[apiBase]);
 const search=useCallback(async(key:string)=>{setActive(key);setQuery(key);setSelected(null);setEdge(null);setLoading(true);setError('');try{const r=await fetch(apiBase+'/api/analysis/search?'+new URLSearchParams({keyword:key,gnn_top_k:'100',include_hypotheses:String(hypotheses)}));if(!r.ok)throw Error('检索失败');setAnalysis(await r.json())}catch(e){setError(String(e))}finally{setLoading(false)}},[apiBase,hypotheses]);
 useEffect(()=>{if(active)void search(active)},[hypotheses]);
 const graph=active?analysis?.kg:all;
 const filtered=useMemo(()=>{let ns=graph?.data.nodes.filter(n=>types.includes(n.type))??[];const ids=new Set(ns.map(n=>n.id));const es=graph?.data.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(hypotheses||e.evidence_status!=='hypothesis'))??[];return {nodes:ns,edges:es}},[graph,types,hypotheses]);
 const chooseNode=useCallback((id:string|null)=>{setSelected(id);setEdge(null)},[]);
 const chooseEdge=useCallback((e:GraphEdge)=>{setEdge(e);setSelected(null)},[]);
 const related=edge?[edge]:selected?filtered.edges.filter(e=>e.source===selected||e.target===selected):[];
 const names=new Map(all?.data.nodes.map(n=>[n.id,n.name]));
 const predictions=analysis?.gnn.predictions??[];
 return <div className="workspace">
  <header className="topbar"><div className="brand-icon"><Network size={22}/></div><div className="brand"><strong>TauClear</strong><span>文献知识图谱与通路筛选</span></div><div className="version"><span/> KG {all?.meta.version??'2.0.0'}<small>2026.10.16</small></div></header>
  <section className="intro"><div><p className="eyebrow">TAU · AUTOPHAGY · LYSOSOME</p><h1>Tau 自噬调控证据网络</h1><p>沿着化合物、分子机制与实验终点，查看可追溯的研究关系。</p></div><div className="stats"><div><strong>{all?.meta.total_nodes??'—'}</strong><span>研究实体</span></div><div><strong>{all?.meta.evidence_edges??'—'}</strong><span>来源可追溯关系</span></div><div><strong>{Object.values(all?.sources??{}).filter(s=>s.url.includes('pubmed')).length||'—'}</strong><span>原始研究</span></div></div></section>
  <div className="main-layout"><aside className="control-panel"><div className="panel-title"><Layers size={17}/><h2>研究对象</h2></div><div className="compound-list">{compoundChoices.map(([id,name])=><button key={id} className={active===id?'active':''} onClick={()=>void search(id)}><span>{name}</span><ChevronRight size={14}/></button>)}</div>
   <form className="searchbox" onSubmit={e=>{e.preventDefault();void search(query)}}><input aria-label="搜索实体或文献编号" placeholder="实体名称、CID、PMID" value={query} onChange={e=>setQuery(e.target.value)}/><button aria-label="搜索"><Search size={17}/></button></form>
   <div className="filter-group"><h3>实体类别</h3>{Object.entries(LABELS).map(([type,label])=><button className={'type-filter '+(types.includes(type)?'on':'')} key={type} onClick={()=>setTypes(t=>t.includes(type)?t.filter(x=>x!==type):[...t,type])}><i style={{background:COLORS[type]}}/>{label}<span>{types.includes(type)&&<Check size={13}/>}</span></button>)}</div>
   <label className="hypothesis-toggle"><input type="checkbox" checked={hypotheses} onChange={e=>setHypotheses(e.target.checked)}/>显示待验证关联</label><p className="muted small">虚线为旧版本保留的机制假设，默认不纳入文献证据层排序。</p>
   <div className="scope-note"><strong>图谱范围</strong><p>所选原始研究与标准数据库。多跳连接用于机制假设，分数不代表有效率。</p></div>
  </aside>
  <section className="network-panel"><div className="graph-heading"><div><h2>{active?(names.get('cpd_'+active)??active)+' · 关联网络':'文献证据网络'}</h2><span>{filtered.nodes.length} 节点 · {filtered.edges.length} 关系</span></div><p>拖拽 · 缩放 · 点击关系查看来源</p></div>{error?<div className="empty">{error}</div>:loading&&!all?<div className="empty">正在读取图谱…</div>:filtered.nodes.length?<EvidenceGraph nodes={filtered.nodes} edges={filtered.edges} selected={selected} onNode={chooseNode} onEdge={chooseEdge}/>:<div className="empty">没有匹配实体</div>}
   <div className="legend">{Object.entries(LABELS).map(([k,v])=><span key={k}><i style={{background:COLORS[k]}}/>{v}</span>)}<span className="line-legend">→ 有向关系</span><span>┄ 待验证关联</span></div>
  </section>
  <aside className="evidence-panel"><div className="panel-title"><BookOpen size={17}/><h2>{selected||edge?'关系与文献':'筛选结果'}</h2></div>
   {related.length>0?<><p className="selection-title">{selected?names.get(selected):'关系详情'}</p><div className="evidence-list">{related.map(e=><article className="evidence-item" key={e.id}><h3>{names.get(e.source)} <span>→</span> {names.get(e.target)}</h3><div className={'badge '+(e.evidence_status==='hypothesis'?'pending':'')}>{e.label} · {e.evidence_status==='hypothesis'?'待验证':e.evidence_status==='annotation'?'数据库注释':'文献实验'}</div><p>{e.context}</p>{e.source_ids?.map(s=>{const ref=all?.sources?.[s];return ref?<a key={s} href={ref.url} target="_blank" rel="noreferrer">{s.match(/^\d+$/)?'PMID '+s:s}<ArrowUpRight size={12}/><span>{ref.title}</span></a>:null})}</article>)}</div></>:!active?<div className="panel-intro"><div className="intro-symbol"><Network size={32}/></div><h3>从一个研究对象出发</h3><p>选择左侧化合物查看通路候选；点击网络中的节点或连线查看对应文献。</p><div className="notice">2024 / 2025 研究已补入 Tau35、自噬通量、内体–溶酶体功能与溶酶体运动关系。</div></div>:<><p className="method-label">EvidenceGraphRank-v2 <span>有向证据排序</span></p>{predictions.length?<div className="prediction-list">{predictions.map((p,i)=><button key={p.node_id} onClick={()=>chooseNode(p.node_id)} className="prediction"><span className="rank">{i+1}</span><div><h3>{p.node_name}</h3><p>{p.hops} 跳 · {p.evidence_status==='hypothesis'?'待验证关联':p.evidence_status==='direct_literature'?'直接文献关系':'跨关系推断'}</p></div><strong>{p.score.toFixed(4)}</strong></button>)}</div>:<div className="notice">{analysis?.molecules.length?"该化合物身份已匹配。当前文献证据层未建立可追溯机制路径；可单独查看待验证关联。":analysis?.kg.data.nodes.length?"当前关键词命中其他研究实体，请点击节点查看文献关系。":"未检索到匹配实体。"}</div>}<div className="notes">{analysis?.notes.map(n=><p key={n}>{n}</p>)}</div></>}
  </aside></div><footer>文献与数据库来源可逐关系查阅 · KG v2.0 · 化合物作用与靶点机制分别记录</footer>
 </div>
}
