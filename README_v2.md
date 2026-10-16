# TauClear 文献知识图谱与通路筛选（KG v2.0）

## 运行

双击 `运行新版.bat`。同一服务同时提供前端和 API，地址为 `http://127.0.0.1:8086/`。

首次在其他电脑使用时，需要 Python 3.10+ 和网络安装 Python 依赖；前端生产构建已包含，无需 Node 即可查看。启动脚本创建本地 `.venv`，只绑定本机地址，不会清空数据库。

手动运行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8086
```

## 目录

- `backend/app/api/routes_v2.py`：当前图谱与分析接口。
- `backend/app/services/literature_graph_service.py`：正式文献图读取与搜索。
- `backend/app/services/evidence_rank_service.py`：有向证据路径排序。
- `backend/data/literature_graph.json`：当前运行图谱，40 节点、51 关系。
- `frontend/src/LiteratureApp.tsx`：新版研究界面。
- `frontend/src/components/EvidenceGraph.tsx`：自然网络布局、方向箭头、分类、拖拽、来源查询及图片导出。
- `frontend/dist/`：可直接由后端提供的前端构建。
- `evidence/raw/`：PubMed、KEGG、UniProt、PubChem 的来源快照。
- `evidence/sources.json`：图谱采用的来源注册表。
- `evidence/evaluation.json`、`test_output.txt`：实际运行、独立重算及自动化测试记录。
- `scripts/`：构图、筛选、绘图与报告复现源码。
- `reports/report-app/`：报告源文件及经验证的编译结果；其维护边界见该目录 `AGENTS.md`。
- `docs/images/literature-kg-v2.svg`、`.png`：与交互图使用相同坐标的正式证据层图。
- `审阅材料/`：仅包含候选结果 CSV、通路结果 CSV、检测报告 PDF 三个文件。

`backend/data/mock_data.json` 及旧模板仅保留用于版本对照，不是新版运行数据源。当前界面不使用旧的环形布局或旧的占位问答模块。

## 数据与方法

49 条正式关系逐条绑定原始研究 / 标准数据库标识，另有 2 条旧关系在假设层隔离。正式来源包含 10 篇原始研究，以及 KEGG、UniProt 的标准注释。2024、2025 年 Tau35 研究分别保留其模型与实验终点。

现有 GNN 兼容接口采用 `EvidenceGraphRank-v2` 固定规则有向路径排序，并非训练型图神经网络。实验边权重 1.00、注释边 0.85；每跳衰减 0.82；最长四跳；取最佳路径。同分项并列解释。待验证关系默认不参与正式排序，显式启用时展示权重 0.25。

跨研究路径用于形成机制假设。分数不代表作用方向、药效、概率、统计显著性或生物学预测准确率。

## 计算复现

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt
.\.venv\Scripts\python.exe scripts\build_literature_kg.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\evaluate_and_export.py
.\.venv\Scripts\python.exe scripts\render_kg_figure.py
```

上述命令重建图谱、运行当前接口、独立枚举路径并重新导出两个结果表。报告的审核数据由 `scripts/prepare_review_report.py` 创建；报告界面采用 `reports/report-app` 的标准构建流程。`scripts/export_review_pdf.py` 从该界面的已构建 HTML 和同一审核数据创建 PDF，保留结论、图示、方法、实际指标及文献来源。当前 PDF 和报告构建均已保存。

前端源码构建需 Node 18+，可使用已有 `pnpm-lock.yaml`：

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm exec tsc -b
pnpm exec vite build
```

## 检测

6 项自动化测试通过；22 条文献层候选分数与独立 NetworkX 枚举实现一致，最大绝对误差 0.0000。未知实体不回退到无关化合物。CID 129908365 在默认文献层为零机制候选，显式假设层单独展示。

Accuracy、Precision、Recall、F1、AUC 未进行生物学独立效能测试。报告中的一致性百分比仅对应表内列明的核验集合。
