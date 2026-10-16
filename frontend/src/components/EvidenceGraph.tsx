import {useEffect,useRef} from 'react';
import * as echarts from 'echarts';
import type {GraphNode,GraphEdge} from '../types/graph';
export const COLORS:Record<string,string>={Compound:'#d99536',Protein:'#8a2856',Gene:'#526474',Pathway:'#258c87',Phenotype:'#9b86aa'};
export const LABELS:Record<string,string>={Compound:'化合物',Protein:'蛋白 / 复合体',Gene:'基因',Pathway:'通路 / 生物过程',Phenotype:'实验终点'};
const escape=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function EvidenceGraph({nodes,edges,selected,onNode,onEdge}:{nodes:GraphNode[];edges:GraphEdge[];selected:string|null;onNode:(n:string|null)=>void;onEdge:(e:GraphEdge)=>void}){
 const element=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!element.current)return;
  const chart=echarts.init(element.current,undefined,{renderer:'canvas'});
  const neighbors=new Set(selected?[selected]:nodes.map(n=>n.id));
  for(const e of edges)if(e.source===selected||e.target===selected){neighbors.add(e.source);neighbors.add(e.target)}
  const nodeMap=new Map(nodes.map(n=>[n.id,n]));
  chart.setOption({backgroundColor:'#fff',animation:false,
   tooltip:{trigger:'item',confine:true,backgroundColor:'#fff',borderColor:'#dce3e8',textStyle:{color:'#243743',fontSize:12},extraCssText:'max-width:360px;white-space:normal;line-height:1.8',formatter:(p:any)=>p.dataType==='edge'?`<b>${escape(nodeMap.get(p.data.source)?.name)} → ${escape(nodeMap.get(p.data.target)?.name)}</b><br/>${escape(p.data.label)}<br/>${escape(p.data.context)}<br/><span style="color:#657785">${escape(p.data.evidence)}</span>`:`<b>${escape(p.data.name)}</b><br/>${escape(LABELS[p.data.nodeType])}<br/>点击查看相邻关系与文献`},
   toolbox:{right:16,top:10,feature:{restore:{title:'恢复视图'},saveAsImage:{title:'导出 KG 图片',name:'TauClear_KG_v2',pixelRatio:3,backgroundColor:'#fff'}}},
   series:[{type:'graph',layout:'none',roam:true,scaleLimit:{min:.35,max:4},left:'8%',right:'10%',top:55,bottom:55,
    data:nodes.map(n=>({id:n.id,name:n.name,nodeType:n.type,x:Number(n.properties.layout_x),y:Number(n.properties.layout_y),symbol:n.type==='Gene'?'diamond':'circle',symbolSize:n.size*.8,draggable:true,itemStyle:{color:COLORS[n.type]??'#80929a',opacity:neighbors.has(n.id)?1:.16,borderWidth:selected===n.id?3:1.5,borderColor:'#fff'},label:{show:true,position:'right',distance:5,color:'#344650',fontFamily:'Microsoft YaHei, sans-serif',fontSize:n.type==='Compound'?12:11,fontWeight:n.type==='Compound'?700:400,backgroundColor:'rgba(255,255,255,0.86)',padding:[2,3]}})),
    links:edges.map(e=>({...e,value:e.type,lineStyle:{color:e.evidence_status==='hypothesis'?'#b7a8bd':'#94abb6',opacity:selected?(neighbors.has(e.source)&&neighbors.has(e.target)?.9:.08):.52,width:e.evidence_status==='experimental'?1.35:1,type:e.evidence_status==='hypothesis'?'dashed':'solid',curveness:.055},label:{show:selected!==null&&(e.source===selected||e.target===selected),position:'middle',distance:3,formatter:e.label??e.type,fontSize:10,color:'#486773',backgroundColor:'rgba(255,255,255,.9)',padding:[2,3]}})),
    // Keep labels in their node/edge coordinate systems; global labelLayout
    // detaches line labels during graph transforms and shifts them off-canvas.
    edgeSymbol:['none','arrow'],edgeSymbolSize:[0,5],emphasis:{focus:'adjacency',label:{show:true},lineStyle:{opacity:1,width:2.5}},blur:{itemStyle:{opacity:.12},lineStyle:{opacity:.06}}}]
  });
  chart.on('click',(p:any)=>{if(p.dataType==='node')onNode(p.data.id===selected?null:p.data.id);if(p.dataType==='edge'){const e=edges.find(e=>e.id===p.data.id);if(e)onEdge(e)}});
  chart.getZr().on('click',(e:any)=>{if(!e.target)onNode(null)});
  const obs=new ResizeObserver(()=>chart.resize());obs.observe(element.current);
  return()=>{obs.disconnect();chart.dispose()};
 },[nodes,edges,selected,onNode,onEdge]);
 return <div ref={element} className="graph-canvas" role="img" aria-label={`文献知识图谱，${nodes.length}个节点，${edges.length}条关系；自然力导向坐标布局`}/>;
}
