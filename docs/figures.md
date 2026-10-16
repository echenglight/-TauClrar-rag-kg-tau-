# 项目科研图

三组项目说明图由 `scripts/render_project_figures.py` 绘制，PNG 用于项目主页，SVG 用于编辑和排版。

| 图 | 内容 | 文件 |
| --- | --- | --- |
| 系统架构 | 来源、知识资产、分析服务、研究界面 | `images/architecture-v2.svg` / `.png` |
| 证据流程 | 标准化、关系整理、证据与假设分层 | `images/evidence-workflow-v2.svg` / `.png` |
| 排序与核验 | 路径评分、候选数量、计算一致性 | `images/ranking-validation-v2.svg` / `.png` |

图中实体与关系计数取自 `backend/data/literature_graph.json`；候选计数取自 `evidence/evaluation.json` 中的独立重算记录。通路计数与测试结果对应审阅材料和 `tests/test_literature_graph.py`。架构描述对应 `backend/app/api/routes_v2.py`、当前服务源码与 `frontend/src/LiteratureApp.tsx`。

`images/literature-kg-v2.svg` / `.png` 由 `scripts/render_kg_figure.py` 绘制，与交互界面使用相同的自然网络坐标。绘图仅使用正式证据边。

上述图为系统实现和计算结果的说明图，不将路径分数或软件一致性转换为生物学有效率。
