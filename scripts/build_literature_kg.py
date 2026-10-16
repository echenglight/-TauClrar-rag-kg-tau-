"""Build a curated, reproducible literature KG. No automatic claim extraction."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,hashlib
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evidence/raw'
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    registry={}
    xml=ET.parse(RAW/'pubmed_selected.xml')
    for item in xml.findall('.//PubmedArticle'):
        med=item.find('MedlineCitation');pmid=med.findtext('PMID');a=med.find('Article')
        doi=next((x.text for x in item.findall('.//ArticleId') if x.get('IdType')=='doi'),'')
        date=a.find('Journal/JournalIssue/PubDate');year=date.findtext('Year') or date.findtext('MedlineDate','')[:4]
        registry[pmid]={'id':pmid,'title':''.join(a.find('ArticleTitle').itertext()),'year':year,'doi':doi,'url':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','source_type':'primary_research'}
    expected=['29967008','21081844','20838929','30108137','21617040','22343943','21258367','32366951','39009859','41399158']
    assert all(k in registry for k in expected)
    for k in ['hsa04140','hsa04142','hsa04150','hsa04151','hsa04152']:
        registry[k]={'id':k,'title':next(x[12:] for x in (RAW/f'KEGG_{k}.txt').read_text(encoding='utf-8-sig').splitlines() if x.startswith('NAME')),'url':f'https://www.kegg.jp/entry/{k}','source_type':'pathway_database'}
    for k in ['Q07869','P19484','P42345','P10636','O75385']:
        raw=json.loads((RAW/f'uniprot_{k}.json').read_text(encoding='utf-8-sig'))
        registry[k]={'id':k,'title':raw['proteinDescription']['recommendedName']['fullName']['value'],'gene':raw['genes'][0]['geneName']['value'],'url':f'https://www.uniprot.org/uniprotkb/{k}/entry','source_type':'protein_database'}
    for cid in ['2244','2519','129908365']:
        row=json.loads((RAW/f'PubChem_{cid}.txt').read_text(encoding='utf-8-sig'))['PropertyTable']['Properties'][0]
        registry['CID:'+cid]={'id':'CID:'+cid,'title':row['Title'],'url':f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}','source_type':'chemical_identity','formula':row['MolecularFormula'],'inchikey':row['InChIKey']}
    nodes=[];edges=[]
    def n(id,name,type,cluster,**props):nodes.append(dict(id=id,name=name,type=type,size=26,properties={'cluster':cluster,**props}))
    for cid,name,cluster in [('2244','阿司匹林','ppara'),('2519','咖啡因','mtor'),('129908365','CID 129908365','candidate')]:
        r=registry['CID:'+cid];n('cpd_'+cid,name,'Compound',cluster,pubchem_cid=cid,formula=r['formula'],inchikey=r['inchikey'],aliases=[cid,r['title']],source_ids=['CID:'+cid])
    genes=[('ppara','PPARA','Q07869','ppara'),('tfeb','TFEB','P19484','tfeb'),('mtor','MTOR','P42345','mtor'),('mapt','MAPT','P10636','tau'),('ulk1','ULK1','O75385','autophagy')]
    for slug,name,accession,cluster in genes:n('gene_'+slug,name+' 基因','Gene',cluster,uniprot=accession,aliases=[name])
    proteins=[('ppara','PPARα','ppara'),('tfeb','TFEB','tfeb'),('mtor','mTOR','mtor'),('mtorc1','mTORC1','mtor'),('akt','AKT','mtor'),('ulk1','ULK1','autophagy'),('ampk','AMPK','autophagy'),('lc3','LC3','autophagy'),('p70','p70S6K','mtor'),('4ebp1','4E-BP1','mtor'),('s6','S6','mtor'),('tau','Tau','tau'),('tau35','Tau35','tau35'),('trpml1','TRPML1','tau'),('ctsd','Cathepsin D','tau35'),('lamp2','LAMP2','tau35')]
    for slug,name,c in proteins:n('prot_'+slug,name,'Protein',c)
    pathways=[('autophagy','自噬过程','autophagy','hsa04140'),('lysosome','溶酶体生物发生','tfeb','hsa04142'),('pi3k','PI3K–AKT 信号','mtor','hsa04151'),('mtor','mTOR 信号','mtor','hsa04150'),('ampk','AMPK 信号','autophagy','hsa04152'),('tau_clearance','Tau 清除相关过程','tau',None),('tau_uptake','胞外 Tau 摄取','tau',None),('tau_exocytosis','Tau 溶酶体外排','tau',None),('endolysosomal','内体–溶酶体功能','tau35',None)]
    for slug,name,c,k in pathways:n('path_'+slug,name,'Pathway',c,standard_id=k,definition='KEGG 功能条目' if k else '文献定义的研究过程；非单一 KEGG 通路')
    for slug,name,c in [('tau_phospho','Tau 磷酸化','tau'),('tau_spread','Tau 病理传播','tau'),('abeta','Aβ 斑块负荷','ppara'),('lipids','脂滴积累','tau35'),('tfeb_nuclear','TFEB 核转位','tfeb'),('autophagosomes','自噬体形成','autophagy'),('lysosome_motility','溶酶体运动','tau35')]:n('pheno_'+slug,name,'Phenotype',c)
    def e(s,t,rel,refs,context,status='experimental',label=None,origin=None):
        assert s in {x['id'] for x in nodes} and t in {x['id'] for x in nodes}
        assert all(r in registry for r in refs)
        edges.append(dict(id=f'lit_{len(edges)+1:03}',source=s,target=t,type=rel,label=label or rel,weight={'experimental':1.0,'annotation':.85,'hypothesis':.25}[status],evidence='; '.join(('PMID:'+r if r.isdigit() else r) for r in refs) or 'Legacy hypothesis; not experimentally validated',source_ids=refs,evidence_status=status,context=context,origin=origin))
    for slug,name,accession,c in genes:e('gene_'+slug,'prot_'+('tau' if slug=='mapt' else slug),'encodes',[accession],'UniProt 人类基因–蛋白登记','annotation','编码')
    e('prot_mtor','prot_mtorc1','component_of',['hsa04150'],'mTORC1 复合体成员','annotation','组成')
    for s,t,k in [('prot_mtor','path_mtor','hsa04150'),('prot_mtorc1','path_mtor','hsa04150'),('prot_akt','path_pi3k','hsa04151'),('prot_ampk','path_ampk','hsa04152'),('prot_ulk1','path_autophagy','hsa04140'),('prot_lc3','path_autophagy','hsa04140'),('prot_ctsd','path_lysosome','hsa04142'),('prot_lamp2','path_lysosome','hsa04142')]:e(s,t,'involved_in',[k],'标准功能条目对应；不代表化合物效应','annotation','参与')
    e('cpd_2244','prot_ppara','activates',['29967008'],'脑细胞 / 5XFAD 小鼠；PPARα 依赖性作用',label='激活')
    e('cpd_2244','prot_tfeb','upregulates',['29967008'],'TFEB 表达上调；不是直接结合实验',label='上调表达')
    e('prot_ppara','prot_tfeb','upregulates',['29967008'],'PPARα 依赖的 Tfeb 转录',label='促进转录')
    e('cpd_2244','path_lysosome','promotes',['29967008'],'细胞及小鼠溶酶体生物发生终点',label='促进')
    e('cpd_2244','pheno_abeta','reduces',['29967008'],'5XFAD 小鼠；Aβ 终点，不等同于 Tau',label='降低')
    e('prot_tfeb','path_lysosome','promotes',['29967008','21617040'],'TFEB 转录调控与溶酶体生物发生',label='促进')
    e('prot_tfeb','path_autophagy','promotes',['21617040'],'TFEB 介导自噬 / 溶酶体协调调控',label='调控')
    e('cpd_2519','prot_akt','inhibits_signaling',['21081844','20838929'],'所研究细胞条件；Akt 信号变化，不表示直接靶点结合',label='降低信号')
    e('cpd_2519','prot_mtorc1','inhibits_signaling',['21081844'],'高浓度细胞处理；Akt/mTOR 下游信号抑制',label='降低信号')
    e('cpd_2519','path_autophagy','promotes',['21081844'],'高浓度细胞研究伴凋亡；效应依赖剂量与细胞条件',label='增强自噬')
    e('cpd_2519','pheno_tau_phospho','modulates',['20838929'],'神经元 / 神经母细胞瘤；磷酸化终点，不等于 Tau 降解',label='调节')
    for p in ['p70','4ebp1','s6']:e('cpd_2519','prot_'+p,'reduces_phosphorylation',['21081844'],'细胞模型中的磷酸化读数，非直接结合证据',label='降低磷酸化')
    e('prot_mtorc1','prot_ulk1','inhibits',['21258367'],'营养条件依赖；Ulk1 Ser757 磷酸化抑制',label='抑制')
    e('prot_ampk','prot_ulk1','activates',['21258367'],'葡萄糖饥饿条件；Ser317 / Ser777；不得外推至所有饥饿条件',label='条件性激活')
    e('prot_ulk1','pheno_autophagosomes','promotes',['21258367'],'自噬启动激酶；特定营养 / 细胞条件',label='促进启动')
    e('pheno_autophagosomes','path_autophagy','part_of',['hsa04140'],'自噬过程的组成阶段','annotation','组成阶段')
    e('prot_mtorc1','pheno_tfeb_nuclear','inhibits',['22343943'],'mTORC1–TFEB 溶酶体营养信号机制',label='抑制核转位')
    e('pheno_tfeb_nuclear','path_lysosome','promotes',['22343943','21617040'],'核内 TFEB 调控溶酶体基因表达',label='促进')
    e('prot_tfeb','path_tau_uptake','promotes',['30108137'],'星形胶质细胞 / 小鼠；胞外 Tau 摄取',label='促进摄取')
    e('prot_tfeb','pheno_tau_spread','reduces',['30108137'],'星形胶质细胞 TFEB 操作；小鼠 Tau 传播模型',label='减弱传播')
    e('prot_tfeb','path_tau_clearance','promotes',['30108137'],'星形胶质细胞中胞外 Tau 摄取和溶酶体清除',label='参与清除')
    e('path_tau_uptake','path_tau_clearance','contributes_to',['30108137'],'摄取与降解分别解释；非药物独立验证',label='相关环节')
    e('prot_tfeb','path_tau_exocytosis','promotes',['32366951'],'截短突变 Tau、缺 MTBR；不同于野生型 Tau 的一般分泌',label='调控外排')
    e('prot_trpml1','path_tau_exocytosis','required_for',['32366951'],'溶酶体钙通道依赖性',label='依赖')
    e('path_tau_exocytosis','path_tau_clearance','contributes_to',['32366951'],'特定不具播种能力 Tau 物种；不概括所有胞外 Tau',label='相关环节')
    e('prot_tau35','prot_tau','fragment_of',['39009859'],'Tau35 为疾病相关 C 端片段；结构关系','annotation','片段')
    e('prot_tau35','pheno_tfeb_nuclear','impairs',['39009859'],'Torin 1 诱导条件；CHO 及原代神经元',label='阻碍核转位')
    e('prot_tau35','pheno_lipids','increases',['39009859'],'CHO / 原代神经元中脂滴积累',label='增加')
    e('prot_tau35','path_autophagy','impairs',['39009859','41399158'],'Tau35 特异模型，自噬通量异常',label='扰动通量')
    e('prot_tau35','path_endolysosomal','impairs',['39009859','41399158'],'不同模型存在不同读数，不代表全部 Tau 物种',label='扰动功能')
    e('prot_tau35','pheno_lysosome_motility','impairs',['41399158'],'2025：Tau35 小鼠 / SH-SY5Y；溶酶体运动受损',label='扰动运动')
    for p in ['ctsd','lamp2']:e('prot_tau35','prot_'+p,'modulates_readout',['39009859'],'CHO 点状信号 / 原代神经元分布读数存在模型差异',label='改变标志物')
    for target in ['prot_ulk1','path_tau_clearance']:e('cpd_129908365',target,'predicted_association',[],'旧版本预置推断；没有本化合物直接机制实验定位','hypothesis','待验证关联','legacy e75/e76')
    # Stable force coordinates; no circular initialization.
    import networkx as nx
    G=nx.Graph();G.add_nodes_from(n['id'] for n in nodes)
    for edge in edges:G.add_edge(edge['source'],edge['target'],weight=.3 if edge['evidence_status']=='hypothesis' else 1)
    pos=nx.spring_layout(G,seed=47,iterations=700,k=.44,scale=1.0)
    for node in nodes:
        node['properties']['layout_x']=round(float(pos[node['id']][0])*600,2)
        node['properties']['layout_y']=round(float(pos[node['id']][1])*420,2)
        node['size']=round(max(16,min(34,16+G.degree(node['id'])*1.3)))
    payload={'meta':{'project':'TauClear Literature KG','version':'2.0.0','as_of':'2026-10-16','scope':'selected_primary_literature_and_standard_annotations','literature_pmids':expected,'node_count':len(nodes),'edge_count':len(edges),'hypothesis_edges':2,'manual_curation':True},'nodes':nodes,'edges':edges,'sources':registry}
    save(ROOT/'backend/data/literature_graph.json',payload)
    save(ROOT/'evidence/sources.json',registry)
    # Preserve the former graph for comparisons only; it is no longer the runtime source.
    old=json.loads((ROOT/'backend/data/mock_data.json').read_text(encoding='utf-8'))
    save(ROOT/'evidence/kg_revision.json',{'old_nodes':len(old['nodes']),'old_edges':len(old['edges']),'new_nodes':len(nodes),'new_edges':len(edges),'strategy':'focused literature rebuild; former unverified relationships are not silently inherited','changes':['增加 PPARα–TFEB 机制','区分 Tau 摄取、传播、磷酸化与外排','纳入 Tau35 2024/2025 研究','CID 129908365 旧机制关系降为可选假设层','每条正式边绑定来源及实验背景'],'source_files':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(RAW.iterdir())]})
    print(json.dumps(payload['meta'],ensure_ascii=False))
if __name__=='__main__':main()
