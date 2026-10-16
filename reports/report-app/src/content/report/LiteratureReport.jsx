import React from 'react';
import {DataComponent,DataTable,ReportSection,RichNarrative,useDataApp} from '../../data-app-public.jsx';
import kgFigure from '../assets/kg-v2.png';
export function ReportContent(){
 const {snapshot,appTitle,visible}=useDataApp();const q=snapshot.queries;
 const previews=Object.fromEntries(q.sources.rows.map(r=>[r.url,{title:r.title,summary:`原始研究；PMID ${r.id}；用于对应模型及实验终点的机制关系定位。`,date:r.year,approvedForReport:true}]));
 const table=(id,title,key,rows,columns)=>visible(id)&&<DataComponent id={id} title={title} kind="table" queryId={key} sourceRows={q[key].rows} displayRows={rows}><DataTable rows={rows} columns={columns.map(key=>({key,label:key}))} compactNumbers={false} searchable={rows.length>10} label={title}/></DataComponent>;
 return <article className="report-content"><header className="report-hero"><h1 data-data-app-title>{appTitle}</h1><RichNarrative id="v2:deck" className="report-deck" value="阿司匹林 · 咖啡因 · CID 129908365｜文献网络重建、机制筛选与系统验证｜2026-10-16"/></header>
 {snapshot.sections.map(s=><React.Fragment key={s.id}>{visible(s.id)&&<ReportSection id={s.id} title={s.title} queryId={s.query} sourceRows={q[s.query].rows} showHeading={false}><RichNarrative id={`v2:${s.id}`} value={`## ${s.title}\n\n${s.text}`} sourcePreviews={previews}/></ReportSection>}
 {s.id==='summary'&&table('overview-table','三个研究对象的筛选概况','overview',q.overview.rows,['化合物','文献层候选','通路 / 生物过程','研究重点'])}
 {s.id==='kg'&&<DataComponent id="kg-figure" title="文献证据网络 · 自然力导向坐标" kind="custom" queryId="graph" sourceRows={q.graph.rows}><figure style={{margin:0}}><img src={kgFigure} alt="40个实体的文献证据网络，采用自然力导向坐标；不含两条待验证关联" style={{width:'100%',height:'auto'}}/><RichNarrative id="v2:figure-caption" value="正式证据层含 49 条有向关系；颜色区分实体类别。化合物、TFEB、自噬及 Tau35 形成可查看来源的局部机制网络。"/></figure></DataComponent>}
 {s.id==='results'&&table('path-table','文献层通路 / 生物过程与候选状态','pathways',q.pathways.rows,['化合物','通路 / 生物过程','规则分数','跳数','证据属性'])}
 {s.id==='validation'&&table('metric-table','实际系统检测结果','metrics',q.metrics.rows,['指标','范围','结果','含义'])}
 {s.id==='references'&&<ReportSection id="source-list" title="参考文献" queryId="sources" sourceRows={q.sources.rows} showHeading={false}><RichNarrative id="v2:source-list" value={q.sources.rows.map(r=>`**[${r.id}] [${r.title}](${r.url})（${r.year}）**\n\nDOI：${r.doi}`).join('\n\n')} sourcePreviews={previews}/></ReportSection>}
 </React.Fragment>)}</article>
}
