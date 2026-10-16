"""Create source-native SVG/PNG figures from the same force coordinates as the UI."""
from pathlib import Path
import json,html,math
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
COLORS={'Compound':'#d99536','Protein':'#8a2856','Gene':'#526474','Pathway':'#258c87','Phenotype':'#9b86aa'}
def render():
    g=json.loads((ROOT/'backend/data/literature_graph.json').read_text(encoding='utf-8'));ns=g['nodes'];es=[e for e in g['edges'] if e['evidence_status']!='hypothesis']
    W,H=1800,1150;coords={n['id']:(n['properties']['layout_x'],n['properties']['layout_y']) for n in ns}
    x0=min(x for x,y in coords.values());x1=max(x for x,y in coords.values());y0=min(y for x,y in coords.values());y1=max(y for x,y in coords.values())
    pts={k:(110+(x-x0)/(x1-x0)*1470,100+(y-y0)/(y1-y0)*850) for k,(x,y) in coords.items()}
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#94abb6"/></marker></defs>']
    for e in es:
        a=pts[e['source']];b=pts[e['target']];dx,dy=b[0]-a[0],b[1]-a[1];d=max(1,math.hypot(dx,dy));start=(a[0]+dx/d*14,a[1]+dy/d*14);end=(b[0]-dx/d*17,b[1]-dy/d*17)
        svg.append(f'<path d="M{start[0]:.1f},{start[1]:.1f} Q{(a[0]+b[0])/2-dy*.045:.1f},{(a[1]+b[1])/2+dx*.045:.1f} {end[0]:.1f},{end[1]:.1f}" fill="none" stroke="#9aafb8" stroke-width="1.8" opacity=".7" marker-end="url(#arrow)"/>')
    # Prioritize compounds and hubs, then choose label positions with fewer overlaps.
    occupied=[]
    degree={n['id']:sum(n['id'] in (e['source'],e['target']) for e in es) for n in ns}
    for n in sorted(ns,key=lambda n:(n['type']!='Compound',-degree[n['id']])):
        x,y=pts[n['id']];r=max(10,min(20,n['size']*.6));color=COLORS[n['type']]
        if n['type']=='Gene':svg.append(f'<path d="M{x},{y-r}L{x+r},{y}L{x},{y+r}L{x-r},{y}Z" fill="{color}" stroke="white" stroke-width="2"/>')
        else:svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="white" stroke-width="2"/>')
        txt=n['name'];font=29 if n['type']=='Compound' else 27;width=sum(font if ord(c)>255 else font*.58 for c in txt)+12;height=39
        candidates=[(x+r+7,y-height/2),(x-r-7-width,y-height/2),(x-width/2,y-r-height-5),(x-width/2,y+r+4),(x+r+7,y+r+8),(x-r-width-7,y-r-height-8)]
        candidates += [(x-width/2,y+offset) for offset in [-105,-80,-60,40,65,90]]
        def penalty(p):
            left,top=p;return sum(max(0,min(left+width,b[0]+b[2])-max(left,b[0]))*max(0,min(top+height,b[1]+b[3])-max(top,b[1])) for b in occupied)+ (10000 if left<20 or left+width>W-20 else 0)
        left,top=min(candidates,key=penalty);occupied.append((left,top,width,height))
        svg.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="white" fill-opacity=".92" rx="3"/><text x="{left+4}" y="{top+height*.77}" font-size="{font}" font-family="Microsoft YaHei, sans-serif" fill="#344650" font-weight="{600 if n["type"]=="Compound" else 400}">{html.escape(txt)}</text>')
    legend=[('Compound','化合物'),('Protein','蛋白 / 复合体'),('Gene','基因'),('Pathway','通路 / 生物过程'),('Phenotype','实验终点')]
    for i,(kind,label) in enumerate(legend):
        x=200+i*300;svg.append(f'<circle cx="{x}" cy="1050" r="9" fill="{COLORS[kind]}"/><text x="{x+18}" y="1058" font-size="23" font-family="Microsoft YaHei" fill="#637a84">{label}</text>')
    svg.append('<text x="900" y="1110" text-anchor="middle" font-size="21" font-family="Microsoft YaHei" fill="#8a9ca3">KG v2.0 · 文献证据层 · 箭头表示关系方向 · 不含两条待验证关联</text></svg>')
    output=ROOT/'docs/images';output.mkdir(exist_ok=True,parents=True);text=''.join(svg);(output/'literature-kg-v2.svg').write_text(text,encoding='utf-8')
    document=pymupdf.open(stream=text.encode(),filetype='svg');pdf=pymupdf.open('pdf',document.convert_to_pdf());pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(output/'literature-kg-v2.png')
    print(output/'literature-kg-v2.png')
if __name__=='__main__':render()
