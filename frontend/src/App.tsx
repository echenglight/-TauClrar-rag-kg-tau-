import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  Search,
  Filter,
  MessageCircle,
  Sparkles,
  Activity,
  Network,
  BrainCircuit,
  TrendingUp
} from "lucide-react";

import {
  chatWithAssistant,
  fetchGraphAll,
  searchIntegrated
} from "./api/graphApi";
import { GraphCanvas } from "./components/GraphCanvas";
import { useTypewriter } from "./hooks/useTypewriter";
import type {
  GNNPrediction,
  GraphEdge,
  GraphNode,
  GraphResponse,
  IntegratedSearchResponse,
  MoleculeProfile
} from "./types/graph";

type LayoutType = "force" | "circular";

interface StatCard {
  label: string;
  value: number;
  suffix?: string;
  icon: JSX.Element;
}

const NODE_TYPE_ZH: Record<string, string> = {
  Gene: "基因",
  Compound: "化合物",
  Pathway: "通路",
  Disease: "疾病",
  Protein: "蛋白",
  Entity: "实体"
};

const EDGE_TYPE_ZH: Record<string, string> = {
  inhibits: "抑制",
  activates: "激活",
  involved_in: "参与",
  modulates: "调节",
  upstream_of: "上游于",
  encodes: "编码",
  interacts_with: "相互作用",
  phosphorylates: "磷酸化",
  assoc_with: "关联",
  associated_with: "相关",
  targets: "靶向"
};

const statCards: StatCard[] = [
  { label: "全球阿尔茨海默病患者", value: 55000000, suffix: "人", icon: <Activity size={18} /> },
  { label: "图谱实体规模", value: 12000, suffix: "+", icon: <Network size={18} /> },
  { label: "整合证据条目", value: 380000, suffix: "+", icon: <Sparkles size={18} /> }
];

function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const steps = 40;
    const perStep = Math.max(1, Math.floor(duration / steps));
    const timer = setInterval(() => {
      frame += 1;
      const next = Math.min(target, Math.round((frame / steps) * target));
      setValue(next);
      if (frame >= steps) {
        clearInterval(timer);
      }
    }, perStep);

    return () => clearInterval(timer);
  }, [duration, target]);

  return value;
}

function StatPanelCard({ card }: { card: StatCard }) {
  const value = useCountUp(card.value);

  return (
    <article className="rounded-2xl border border-cyan-100 bg-white p-5 shadow-[0_14px_32px_-18px_rgba(7,44,79,0.42)]">
      <div className="mb-4 inline-flex rounded-xl bg-cyan-100/70 p-2 text-cyan-800">{card.icon}</div>
      <p className="text-sm text-slate-500">{card.label}</p>
      <p className="mt-2 text-3xl font-extrabold text-[#0f2747]">
        {value.toLocaleString()}
        <span className="ml-1 text-lg font-semibold text-cyan-700">{card.suffix || ""}</span>
      </p>
    </article>
  );
}

function App() {
  const [loading, setLoading] = useState(true);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<IntegratedSearchResponse | null>(null);
  const [dataHint, setDataHint] = useState("");
  const [keyword, setKeyword] = useState("");
  const [layout, setLayout] = useState<LayoutType>("force");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  const [selectedEdgeTypes, setSelectedEdgeTypes] = useState<string[]>([]);

  const [question, setQuestion] = useState("");
  const [assistantReply, setAssistantReply] = useState(
    "你好，我是 TauClear 智能助手。你可以问我：某个基因如何影响 Tau 清除通路？"
  );
  const [replyLoading, setReplyLoading] = useState(false);
  const [chatSource, setChatSource] = useState<"dify" | "local_llm">("dify");

  const animatedReply = useTypewriter(assistantReply, 11);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        try {
          const data = await fetchGraphAll();
          setGraph(data);
          setDataHint("");
        } catch {
          setDataHint("后端图谱接口未连通，请确认 8000 端口服务已启动。");
        }

        const [analysisResultResp] = await Promise.allSettled([searchIntegrated("")]);

        if (analysisResultResp.status === "fulfilled") {
          setAnalysisResult(analysisResultResp.value);
        } else {
          setDataHint((prev) => prev || "分析接口未返回，已显示默认图谱。重启后端可恢复分子指纹与GNN。");
        }
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const nodeTypes = useMemo(() => {
    if (!graph) {
      return [];
    }
    return Object.keys(graph.meta.node_type_stats);
  }, [graph]);

  const edgeTypes = useMemo(() => {
    if (!graph) {
      return [];
    }
    return Object.keys(graph.meta.edge_type_stats);
  }, [graph]);

  useEffect(() => {
    if (!graph) {
      return;
    }
    setSelectedNodeTypes(Object.keys(graph.meta.node_type_stats));
    setSelectedEdgeTypes(Object.keys(graph.meta.edge_type_stats));
  }, [graph]);

  const filtered = useMemo(() => {
    if (!graph) {
      return { nodes: [] as GraphNode[], edges: [] as GraphEdge[] };
    }

    const allowedNodes = graph.data.nodes.filter((n) => selectedNodeTypes.includes(n.type));
    const idSet = new Set(allowedNodes.map((n) => n.id));
    const allowedEdges = graph.data.edges.filter(
      (e) => selectedEdgeTypes.includes(e.type) && idSet.has(e.source) && idSet.has(e.target)
    );

    return {
      nodes: allowedNodes,
      edges: allowedEdges
    };
  }, [graph, selectedEdgeTypes, selectedNodeTypes]);

  const selectedNodeName = useMemo(() => {
    if (!selectedNodeId) {
      return "无";
    }
    const node = filtered.nodes.find((n) => n.id === selectedNodeId);
    return node?.name || selectedNodeId;
  }, [filtered.nodes, selectedNodeId]);

  const toggleItem = (arr: string[], item: string) =>
    arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item];

  const gnnPredictions = analysisResult?.gnn?.predictions || [];
  const gnnMaxScore = useMemo(() => {
    if (!gnnPredictions.length) {
      return 1;
    }
    return Math.max(...gnnPredictions.map((p) => p.score), 1);
  }, [gnnPredictions]);

  const onSearch = async () => {
    setLoading(true);
    try {
      if (keyword.trim()) {
        const data = await searchIntegrated(keyword.trim());
        setGraph(data.kg);
        setAnalysisResult(data);
      } else {
        const data = await fetchGraphAll();
        setGraph(data);
      }
      setSelectedNodeId(null);
    } finally {
      setLoading(false);
    }
  };

  const renderMoleculeCard = (molecule: MoleculeProfile) => {
    const descriptorEntries = Object.entries(molecule.descriptors);
    return (
      <article key={molecule.name} className="rounded-xl border border-cyan-100 bg-cyan-50/40 p-3">
        <p className="text-sm font-bold text-[#0f2747]">{molecule.name}</p>
        <p className="mt-1 text-xs text-slate-600">分子式：{molecule.molecular_formula || "-"}</p>
        <p className="mt-1 break-all text-[11px] text-slate-500">SMILES：{molecule.smiles || "-"}</p>
        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg bg-white px-2 py-1 text-slate-700">
            Morgan 置位数：{molecule.fingerprint.morgan_on_bits}
          </div>
          <div className="rounded-lg bg-white px-2 py-1 text-slate-700">
            MACCS 置位数：{molecule.fingerprint.maccs_on_bits}
          </div>
        </div>
        <p className="mt-2 text-[11px] text-slate-600">
          Morgan 位点预览：{molecule.fingerprint.morgan_on_indices_preview.join(", ") || "-"}
        </p>
        {descriptorEntries.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {descriptorEntries.slice(0, 6).map(([k, v]) => (
              <span key={k} className="rounded-full bg-white px-2 py-1 text-[11px] text-slate-700">
                {k}:{String(v)}
              </span>
            ))}
          </div>
        )}
      </article>
    );
  };

  const renderGNNItem = (prediction: GNNPrediction, index: number) => {
    const nodeTypeColor: Record<string, string> = {
      Pathway: "text-teal-700 bg-teal-50 border-teal-200",
      Gene: "text-blue-700 bg-blue-50 border-blue-200",
      Disease: "text-rose-700 bg-rose-50 border-rose-200",
      Protein: "text-slate-700 bg-slate-50 border-slate-200"
    };
    const scorePercent = Math.max(8, Math.round((prediction.score / gnnMaxScore) * 100));

    return (
      <div
        key={prediction.node_id}
        className="rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-50/70 via-white to-cyan-50/70 p-3 shadow-sm"
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#0f2747] text-xs font-bold text-white">
              {index + 1}
            </span>
            <p className="text-base font-bold text-[#0f2747]">{prediction.node_name}</p>
          </div>
          <span
            className={`rounded-full border px-2.5 py-0.5 text-xs ${nodeTypeColor[prediction.node_type] || "text-sky-700 bg-sky-50 border-sky-200"
              }`}
          >
            {prediction.node_type}
          </span>
        </div>

        <div className="mb-2 flex items-center justify-between text-xs text-slate-600">
          <span className="inline-flex items-center gap-1">
            <TrendingUp size={12} /> 预测得分
          </span>
          <span className="font-semibold text-[#0f2747]">{prediction.score.toFixed(4)}</span>
        </div>

        <div className="mb-2 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-sky-500 to-blue-600"
            style={{ width: `${scorePercent}%` }}
          />
        </div>

        <p className="text-[11px] leading-relaxed text-slate-600">{prediction.explanation}</p>
      </div>
    );
  };

  const onAsk = async () => {
    if (!question.trim()) {
      return;
    }
    setReplyLoading(true);
    try {
      const reply = await chatWithAssistant({
        question,
        source: chatSource,
        top_k: 8,
        temperature: 0.2,
        session_id: "demo-session"
      });
      setAssistantReply(reply);
      setQuestion("");
    } finally {
      setReplyLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="relative overflow-hidden bg-gradient-to-br from-[#06162a] via-[#0b2d4f] to-[#13839a]">
        <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(#9ee7ff_1.1px,transparent_1.1px)] [background-size:28px_28px]" />
        <div className="relative mx-auto flex max-w-7xl flex-col px-6 pb-24 pt-20 lg:flex-row lg:items-end lg:justify-between lg:pb-28">
          <div className="max-w-3xl">
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-200/40 bg-cyan-200/10 px-4 py-1 text-sm text-cyan-100">
              <Sparkles size={14} /> 医学知识图谱智能平台
            </p>
            <h1 className="text-4xl font-black leading-tight text-white md:text-6xl">
              Tau 蛋白自噬调控通路
              <span className="block bg-gradient-to-r from-cyan-200 to-sky-300 bg-clip-text text-transparent">
                可视化与智能问答中枢
              </span>
            </h1>
            <p className="mt-5 max-w-2xl text-base text-cyan-50/90 md:text-lg">
              通过多源证据融合、图谱深度交互和大模型辅助问答，快速定位潜在药物靶点、关键通路与疾病关联。
            </p>
          </div>
        </div>
      </div>

      <main className="relative z-10 mx-auto -mt-4 max-w-[1800px] space-y-8 px-4 pb-10 md:-mt-6 md:px-6 lg:-mt-10">
        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {statCards.map((card) => (
            <StatPanelCard key={card.label} card={card} />
          ))}
        </section>

        <section className="grid grid-cols-1 gap-6 xl:grid-cols-[430px_minmax(0,1fr)_430px]">
          <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-2 text-[#0f2747]">
              <Filter size={17} />
              <h2 className="text-lg font-bold">图谱控制台</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">实体搜索</label>
                <p className="mb-2 text-xs text-slate-500">输入关键词后，系统自动输出知识图谱、分子指纹和图神经网络候选。</p>
                <div className="flex gap-2">
                  <input
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="输入基因、化合物、疾病..."
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={onSearch}
                    className="rounded-xl bg-[#0f2747] px-3 text-white transition hover:bg-[#12345e]"
                  >
                    <Search size={16} />
                  </button>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">布局算法</label>
                <div className="grid grid-cols-2 gap-2">
                  {(["force", "circular"] as LayoutType[]).map((item) => (
                    <button
                      key={item}
                      onClick={() => setLayout(item)}
                      className={`rounded-lg border px-3 py-2 text-sm ${layout === item
                        ? "border-cyan-500 bg-cyan-50 text-cyan-800"
                        : "border-slate-300 text-slate-600"
                        }`}
                    >
                      {item === "force" ? "力导向" : "环形"}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-700">节点类型过滤</h3>
                <div className="flex flex-wrap gap-2">
                  {nodeTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => setSelectedNodeTypes((prev) => toggleItem(prev, type))}
                      className={`rounded-full px-3 py-1 text-xs ${selectedNodeTypes.includes(type)
                        ? "bg-cyan-100 text-cyan-900"
                        : "bg-slate-100 text-slate-500"
                        }`}
                    >
                      {NODE_TYPE_ZH[type] || type}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-700">关系类型过滤</h3>
                <div className="flex max-h-44 flex-wrap gap-2 overflow-auto">
                  {edgeTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => setSelectedEdgeTypes((prev) => toggleItem(prev, type))}
                      className={`rounded-full px-3 py-1 text-xs ${selectedEdgeTypes.includes(type)
                        ? "bg-sky-100 text-sky-900"
                        : "bg-slate-100 text-slate-500"
                        }`}
                    >
                      {EDGE_TYPE_ZH[type] || type}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                {graph ? (
                  <>
                    <p>当前节点数：{filtered.nodes.length}</p>
                    <p>当前关系数：{filtered.edges.length}</p>
                    <p>已选节点：{selectedNodeName}</p>
                  </>
                ) : (
                  <p>{loading ? "正在加载图谱..." : dataHint || "未加载到图谱数据"}</p>
                )}
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-3">
                <h3 className="text-sm font-semibold text-slate-700">分子指纹结果</h3>
                {analysisResult?.molecules?.length ? (
                  <div className="max-h-[340px] space-y-3 overflow-auto pr-1">
                    {analysisResult.molecules.map(renderMoleculeCard)}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">未加载到分子文件结果，请检查示例分子文件路径。</p>
                )}
              </div>

              <div className="space-y-2 border-t border-slate-100 pt-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-700">图神经网络候选</h3>
                  <span className="inline-flex items-center gap-1 rounded-full bg-cyan-50 px-2 py-0.5 text-[11px] text-cyan-800">
                    <BrainCircuit size={12} /> {analysisResult?.gnn?.model_name || "LightGNN"}
                  </span>
                </div>
                {analysisResult?.gnn?.predictions?.length ? (
                  <div className="max-h-[340px] space-y-3 overflow-auto pr-1">
                    {analysisResult.gnn.predictions.map((item, idx) => renderGNNItem(item, idx))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">暂无候选，请更换关键词后重试。</p>
                )}
              </div>

              {dataHint ? (
                <div className="rounded-xl bg-rose-50 p-2 text-[11px] text-rose-700">{dataHint}</div>
              ) : null}
            </div>
          </aside>

          <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="mb-2 flex items-center justify-between px-2">
              <h2 className="text-lg font-bold text-[#0f2747]">交互式知识图谱</h2>
              <p className="text-xs text-slate-500">支持缩放、拖拽、邻居高亮、关系过滤</p>
            </div>
            {loading ? (
              <div className="flex h-[1200px] items-center justify-center text-slate-500 xl:h-[1320px]">图谱加载中...</div>
            ) : (
              <GraphCanvas
                nodes={filtered.nodes}
                edges={filtered.edges}
                layout={layout}
                selectedNodeId={selectedNodeId}
                onNodeClick={setSelectedNodeId}
              />
            )}
          </section>

          <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2 text-[#0f2747]">
              <MessageCircle size={17} />
              <h2 className="text-lg font-bold">智能问答</h2>
            </div>

            <div className="mb-3 flex gap-2">
              {(["dify", "local_llm"] as const).map((source) => (
                <button
                  key={source}
                  onClick={() => setChatSource(source)}
                  className={`rounded-lg border px-3 py-1.5 text-xs ${chatSource === source
                    ? "border-cyan-500 bg-cyan-50 text-cyan-800"
                    : "border-slate-300 text-slate-500"
                    }`}
                >
                  {source === "dify" ? "Dify 网关" : "本地 LLM"}
                </button>
              ))}
            </div>

            <div className="mb-3 h-[420px] overflow-auto rounded-xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-3">
              <div className="mb-3 flex items-start gap-2">
                <div className="mt-0.5 rounded-full bg-[#0f2747] p-1 text-white">
                  <Bot size={14} />
                </div>
                <div className="prose prose-sm max-w-none text-slate-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{animatedReply}</ReactMarkdown>
                </div>
              </div>
              {replyLoading && <p className="text-xs text-slate-400">模型思考中...</p>}
            </div>

            <div className="space-y-2">
              <textarea
                rows={4}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="例如：Rapamycin 如何影响 Tau 蛋白清除？"
                className="w-full resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-500"
              />
              <button
                onClick={onAsk}
                className="w-full rounded-xl bg-gradient-to-r from-[#0f2747] to-[#13839a] px-3 py-2 text-sm font-semibold text-white"
              >
                发送问题
              </button>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

export default App;
