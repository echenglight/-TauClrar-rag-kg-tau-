"""Export verified report HTML + its reviewed snapshot, omitting app controls."""
from pathlib import Path
import json,re,html,hashlib
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[1];APP=ROOT/'reports/report-app'
assert (APP/'dist/index.html').is_file()
data=json.loads((APP/'src/data.json').read_text(encoding='utf-8'));assert data['buildStatus']=='complete'
FONT=Path('C:/Windows/Fonts');pdfmetrics.registerFont(TTFont('CN',str(FONT/'msyh.ttc'),subfontIndex=0));pdfmetrics.registerFont(TTFont('CN-Bold',str(FONT/'msyhbd.ttc'),subfontIndex=0));pdfmetrics.registerFontFamily('CN',normal='CN',bold='CN-Bold',italic='CN',boldItalic='CN-Bold')
INK=colors.HexColor('#233d46');MUTED=colors.HexColor('#657c86');GREEN=colors.HexColor('#23837e')
styles={
 'title':ParagraphStyle('Title',fontName='CN-Bold',fontSize=21,leading=31,textColor=INK,spaceAfter=17),
 'h':ParagraphStyle('Heading',fontName='CN-Bold',fontSize=13,leading=21,textColor=INK,spaceAfter=11,spaceBefore=5,keepWithNext=True),
 'body':ParagraphStyle('Body',fontName='CN',fontSize=9.4,leading=16,textColor=INK,spaceAfter=11,wordWrap='CJK'),
 'small':ParagraphStyle('Small',fontName='CN',fontSize=8,leading=12.7,textColor=MUTED,spaceAfter=8,wordWrap='CJK'),
 'cell':ParagraphStyle('Cell',fontName='CN',fontSize=8.2,leading=12.5,textColor=INK,wordWrap='CJK'),
 'head':ParagraphStyle('Head',fontName='CN-Bold',fontSize=8.2,leading=12.5,textColor=INK,wordWrap='CJK')}
def p(t,kind='body'):
    t=html.escape(str(t));t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t);t=re.sub(r'`([^`]+)`',r'\1',t)
    return Paragraph(t,styles[kind])
story=[];secs={s['id']:s for s in data['sections']};q=data['queries']
def add(id):
    s=secs[id];story.append(p(s['title'],'h'))
    story.extend(p(t) for t in s['text'].split('\n\n'))
def table(rows,fields,widths):
    values=[[p(f,'head') for f in fields]]+[[p(r.get(f,''),'cell') for f in fields] for r in rows]
    t=Table(values,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf5f3')),('LINEBELOW',(0,0),(-1,0),.7,GREEN),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#dce6e7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.extend([t,Spacer(1,12)])
def page():story.append(PageBreak())
story.append(p('Tau 自噬相关通路筛选\n与系统验证报告'.replace('\n',' '),'title'));story.append(p('KG v2.0  |  阿司匹林 · 咖啡因 · CID 129908365  |  2026-10-16','small'))
add('summary');table(q['overview']['rows'],['化合物','文献层候选','通路 / 生物过程','研究重点'],[105,65,80,225])
page();add('kg');story.append(Image(str(ROOT/'docs/images/literature-kg-v2.png'),width=475,height=475*1150/1800));story.append(p('图 1　新版文献证据网络。采用与交互图一致的自然力导向坐标，展示 40 个实体及 49 条正式关系；CID 129908365 在该层仅显示化学身份。两条旧假设关系未绘入本图。','small'))
page();add('method')
story.append(p('主要候选实体（完整结果见候选结果表）','h'))
tops=[]
for cid in ['2244','2519']:
    tops.extend([r for r in q['candidates']['rows'] if r['PubChem CID']==cid][:4])
table(tops,['化合物','候选实体','规则分数','证据属性'],[90,155,70,160])
page();add('results');table(q['pathways']['rows'],['化合物','通路 / 生物过程','规则分数','跳数','证据属性'],[90,145,65,35,140])
page();add('interpretation');add('validation');table(q['metrics']['rows'],['指标','范围','结果','含义'],[105,125,95,150])
page();add('references')
for ref in q['sources']['rows']:
    block=[p(f'[{ref["id"]}] {ref["title"]} ({ref["year"]}).','small'),Paragraph(f'<link href="{html.escape(ref["url"])}" color="#23837e">PMID {ref["id"]}</link>  ·  DOI: {html.escape(ref["doi"])}',styles['small'])]
    story.append(KeepTogether(block))
story.append(Spacer(1,6));story.append(p('公开数据库：KEGG（https://www.kegg.jp/）；UniProt（https://www.uniprot.org/）；PubChem（https://pubchem.ncbi.nlm.nih.gov/）。标准标识保存在相应图谱关系及筛选结果中。','small'))
def footer(c,doc):
    w,h=doc.pagesize;c.saveState();c.setStrokeColor(colors.HexColor('#dce6e7'));c.line(42,h-33,w-42,h-33);c.setFont('CN',8);c.setFillColor(MUTED);c.drawString(42,h-24,'TauClear  /  文献知识图谱与系统验证');c.drawString(42,24,'KG v2.0  |  2026-10-16');c.drawRightString(w-42,24,str(doc.page));c.restoreState()
out=ROOT/'审阅材料/通路筛选与系统检测报告.pdf'
SimpleDocTemplate(str(out),pagesize=(595.28,841.89),leftMargin=60,rightMargin=60,topMargin=51,bottomMargin=45,title=data['title'],author='TauClear').build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'evidence/pdf_export.json').write_text(json.dumps({'source_html':str(APP/'dist/index.html'),'html_sha256':hashlib.sha256((APP/'dist/index.html').read_bytes()).hexdigest(),'snapshot_sha256':hashlib.sha256((APP/'src/data.json').read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'browser_text_edits':'none'},ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
