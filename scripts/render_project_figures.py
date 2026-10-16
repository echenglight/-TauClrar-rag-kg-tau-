"""Render repository figures as editable SVG and high-resolution PNG.

Counts are read from the curated KG and the independent evaluation record.
Architecture and ranking rules correspond to the v2 source code.
"""
from pathlib import Path
from collections import Counter
import html
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/images'
INK, MUTED, RULE = '#263b45', '#6c7e89', '#dce5e9'
TEAL, BERRY, GOLD, BLUE = '#258c87', '#8a2856', '#d99536', '#526474'
FONT = Path('C:/Windows/Fonts/msyh.ttc')
if not FONT.exists():
    candidates = [Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
                  Path('/System/Library/Fonts/PingFang.ttc')]
    FONT = next((p for p in candidates if p.exists()), FONT)


class Figure:
    def __init__(self, height, title, subtitle):
        self.width, self.height = 1600, height
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}" role="img"><title>{html.escape(title)}</title><desc>{html.escape(subtitle)}</desc><rect width="100%" height="100%" fill="white"/>']
        self.image = Image.new('RGB', (1600, height), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.text(60, 42, 'TAUCLEAR  /  KG v2.0', 20, TEAL)
        self.text(60, 86, title, 40)
        self.text(60, 144, subtitle, 22, MUTED)
        self.line([(60, 188), (1540, 188)], RULE, 2)

    def text(self, x, y, text, size=24, color=INK, bold=False):
        font = ImageFont.truetype(str(FONT), size)
        self.draw.text((x, y), text, font=font, fill=color, anchor='lt', stroke_width=0)
        self.svg.append(f'<text x="{x}" y="{y+size*.88}" fill="{color}" font-size="{size}" font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif" font-weight="{600 if bold else 400}">{html.escape(str(text))}</text>')

    def rect(self, x, y, w, h, fill='white', stroke=RULE, radius=12):
        self.draw.rounded_rectangle((x, y, x+w, y+h), radius, fill, stroke, 2)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

    def line(self, points, color=MUTED, width=2, arrow=False, dashed=False):
        for a, b in zip(points, points[1:]):
            if dashed:
                distance = math.dist(a, b)
                for step in range(0, int(distance), 14):
                    t, u = step/max(distance, 1), min(step+7, distance)/max(distance, 1)
                    self.draw.line([(a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t), (a[0]+(b[0]-a[0])*u, a[1]+(b[1]-a[1])*u)], fill=color, width=width)
            else:
                self.draw.line([a, b], fill=color, width=width)
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 7"' if dashed else '')+'/>')
        if arrow:
            a, b = points[-2:]; angle = math.atan2(b[1]-a[1], b[0]-a[0])
            p = [b, (b[0]-12*math.cos(angle-.5), b[1]-12*math.sin(angle-.5)), (b[0]-12*math.cos(angle+.5), b[1]-12*math.sin(angle+.5))]
            self.draw.polygon(p, fill=color)
            self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in p)}" fill="{color}"/>')

    def card(self, x, y, w, h, title, lines, color=TEAL, fill='#f7fafb'):
        self.rect(x, y, w, h, fill)
        self.line([(x+20, y+23), (x+20, y+48)], color, 4)
        self.text(x+35, y+21, title, 27, color, True)
        for i, text in enumerate(lines):
            self.text(x+24, y+69+i*31, text, 21, MUTED)

    def save(self, name):
        self.svg.append('</svg>')
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/f'{name}.svg').write_text(''.join(self.svg), encoding='utf-8')
        self.image.save(OUT/f'{name}.png', dpi=(240, 240))


def render():
    kg = json.loads((ROOT/'backend/data/literature_graph.json').read_text(encoding='utf-8'))
    evaluation = json.loads((ROOT/'evidence/evaluation.json').read_text(encoding='utf-8'))
    formal = sum(e['evidence_status'] != 'hypothesis' for e in kg['edges'])
    hypotheses = len(kg['edges'])-formal
    counts = Counter(r['cid'] for r in evaluation['score_records'])
    n = len(kg['nodes'])

    f = Figure(1120, '文献证据驱动的系统架构', '从公开研究到可追溯关系、通路候选与审阅结果；展示当前版本的实际运行链路。')
    rows = [
        (225, '01  证据来源', TEAL, [
            ('原始研究', ['PubMed 原始研究 10 篇', '保留实验模型与研究终点']),
            ('标准数据库', ['PubChem · KEGG · UniProt', '化合物身份、通路与基因注释']),
            ('本地分子资料', ['3 个 CID 的描述符与指纹', '原始快照、标识及文件留存'])]),
        (425, '02  知识组织', BLUE, [
            ('文献知识图谱', [f'{n} 个实体 · {formal} 条正式关系', '有向边、关系类型与来源索引']),
            ('证据与假设分层', [f'{hypotheses} 条旧机制假设独立保存', '默认排除；显式启用后单列']),
            ('可复现数据资产', ['JSON 图谱与来源注册表', '分子数据表与公开来源快照'])]),
        (625, '03  分析服务', BERRY, [
            ('FastAPI 接口', ['实体检索与邻域查询', '图谱、来源与分析结果编排']),
            ('EvidenceGraphRank-v2', ['最长 4 跳的有向路径排序', '固定权重与逐跳衰减']),
            ('结果与核验', ['候选和通路表导出', '独立重算、来源与隔离测试'])]),
        (825, '04  研究界面', TEAL, [
            ('React + TypeScript', ['化合物切换、搜索与类别筛选', '通过同源 API 读取结果']),
            ('ECharts 证据网络', ['自然网络布局、拖拽与缩放', '节点 / 连线联动文献详情']),
            ('三份审阅材料', ['模块结果 CSV · 通路结果 CSV', '系统检测报告 PDF'])])]
    for y, label, color, cards in rows:
        f.text(60, y+47, label, 24, color, True)
        for x, (title, lines) in zip([285, 710, 1135], cards):
            f.card(x, y, 405, 150, title, lines, color)
        if y != 825:
            for x in [488, 913, 1338]:
                f.line([(x, y+152), (x, y+195)], '#9cb0b9', 2, True)
    f.text(60, 1030, '实现边界：当前排序采用确定性证据路径规则；旧版 RAG / Neo4j 接入代码保留供版本对照。', 23, MUTED)
    f.save('architecture-v2')

    f = Figure(1100, '知识图谱构建与证据分层流程', '正式证据与待验证关联分别处理；每条正式关系均保留来源标识与研究语境。')
    stages = [
        ('01  身份与来源', ['核对 3 个 PubChem CID', '汇集 10 篇原始研究']),
        ('02  实体标准化', ['化合物 / 蛋白 / 基因', '通路与实验终点分开建模']),
        ('03  关系整理', ['记录方向、类型与实验背景', '绑定 PMID / 标准数据库 ID']),
        ('04  图谱核验', [f'{n} 个节点 · {len(kg["edges"])} 条总关系', '检查重复、端点与来源绑定'])]
    for i, (title, lines) in enumerate(stages):
        x = 60+i*390
        f.card(x, 230, 310, 165, title, lines)
        if i < 3:
            f.line([(x+315, 312), (x+382, 312)], TEAL, 2, True)
    f.line([(1385, 397), (1385, 432), (410, 432), (410, 478)], BLUE, 2, True)
    f.line([(1385, 432), (1190, 432), (1190, 478)], GOLD, 2, True, True)
    f.card(60, 485, 700, 215, f'正式证据层  /  {formal} 条关系', [
        '实验关系权重 1.00；数据库注释权重 0.85',
        '默认纳入有向路径排序，保留原始模型与终点',
        '跨研究连接用于机制线索，不能替代实验验证'], TEAL)
    f.card(840, 485, 700, 215, f'待验证假设层  /  {hypotheses} 条关系', [
        '旧版机制关联单列，权重 0.25',
        '默认关闭；仅在显式开启时展示',
        'CID 129908365 默认无正式机制候选'], GOLD, '#fcfaf5')
    f.line([(410, 702), (410, 765), (290, 765), (290, 817)], TEAL, 2, True)
    f.line([(410, 765), (800, 765), (800, 817)], TEAL, 2, True)
    f.line([(800, 765), (1310, 765), (1310, 817)], TEAL, 2, True)
    f.card(60, 825, 460, 150, '候选结果', [f'{sum(counts.values())} 个文献层候选', '逐项保留路径、跳数与来源'], TEAL)
    f.card(570, 825, 460, 150, '通路筛选', ['9 条化合物–通路候选', '阿司匹林 5 条；咖啡因 4 条'], TEAL)
    f.card(1080, 825, 460, 150, '系统核验', ['独立路径重算与功能测试', '结果表、检测报告与证据快照'], TEAL)
    f.text(60, 1030, '统计口径：22 个候选和 9 条通路均不含第三 CID 的状态说明行，亦不含假设层结果。', 22, MUTED)
    f.save('evidence-workflow-v2')

    f = Figure(1050, '有向证据排序与计算核验', '评分表示路径在当前规则下的相对排序；不是概率、药效或生物学预测准确率。')
    f.rect(60, 225, 850, 445, '#f7fafb')
    f.text(90, 255, '候选得分：取所有有效路径的最大值', 28, TEAL, True)
    f.text(90, 310, 'score = max [ (w1 × … × wh) × 0.82^(h − 1) ]', 27)
    f.text(90, 363, 'h ≤ 4；沿箭头方向；路径中不重复节点', 23, MUTED)
    for x, label, color in [(100, '阿司匹林', GOLD), (380, 'TFEB', BERRY), (660, '自噬过程', TEAL)]:
        f.rect(x, 445, 200, 70, 'white', color)
        f.text(x+26, 466, label, 25, color)
    for x in [300, 580]:
        f.line([(x+5, 480), (x+72, 480)], BLUE, 2, True)
        f.text(x+10, 417, '1.00', 20, MUTED)
    f.text(100, 550, '示例：1.00 × 1.00 × 0.82 = 0.8200', 27)
    f.text(100, 604, '来源：PMID 29967008 / 21617040', 22, MUTED)
    f.text(970, 246, '文献层候选数', 28, TEAL, True)
    chart_x, chart_w = 1140, 330
    for i, (cid, label) in enumerate([('2244', '阿司匹林'), ('2519', '咖啡因'), ('129908365', '第三 CID')]):
        y = 342+i*100; count = counts[cid]
        f.text(970, y, label, 23)
        if count:
            f.rect(chart_x, y, chart_w*count/15, 36, TEAL, TEAL, 0)
        f.text(chart_x+chart_w*count/15+12, y+2, str(count), 25, TEAL)
    f.line([(chart_x, 318), (chart_x, 590)], RULE, 2)
    for tick in [0, 5, 10, 15]:
        x = chart_x+chart_w*tick/15
        f.text(x-7, 612, str(tick), 19, MUTED)
    f.text(970, 644, '计数单位：候选实体；假设层关闭', 20, MUTED)
    metrics = [('来源绑定', f'{formal}/{formal}', '正式关系均有来源标识'),
               ('分数独立重算', '22/22', '与 NetworkX 枚举一致'),
               ('功能 / 方法测试', '6/6', '方向、权重、来源与隔离'),
               ('最大绝对误差', '0.0000', '22 条候选的四位小数分数')]
    for i, (label, value, note) in enumerate(metrics):
        x = 60+i*380
        f.rect(x, 735, 340, 190)
        f.text(x+23, 759, label, 23, MUTED)
        f.text(x+23, 806, value, 42, TEAL, True)
        f.text(x+23, 876, note, 19, MUTED)
    f.text(60, 981, '核验范围：软件与计算一致性；尚未建立用于 Accuracy、Precision、Recall、F1、AUC 的独立标注集。', 21, MUTED)
    f.save('ranking-validation-v2')
    print('Rendered 3 figures as SVG + PNG from the curated KG and evaluation record.')


if __name__ == '__main__':
    render()
