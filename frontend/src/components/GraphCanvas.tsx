import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts";
import type { GraphEdge, GraphNode } from "../types/graph";

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  layout: "force" | "circular";
  selectedNodeId: string | null;
  onNodeClick: (nodeId: string | null) => void;
}

const palette: Record<string, string> = {
  Gene: "#21c3d9",
  Compound: "#3b82f6",
  Pathway: "#0ea5a4",
  Disease: "#f87171",
  Protein: "#94a3b8",
  Entity: "#60a5fa"
};

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

export function GraphCanvas({
  nodes,
  edges,
  layout,
  selectedNodeId,
  onNodeClick
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const nodeNameMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const n of nodes) {
      map.set(n.id, n.name);
    }
    return map;
  }, [nodes]);

  const neighbors = useMemo(() => {
    if (!selectedNodeId) {
      return new Set<string>();
    }
    const set = new Set<string>([selectedNodeId]);
    for (const e of edges) {
      if (e.source === selectedNodeId) {
        set.add(e.target);
      }
      if (e.target === selectedNodeId) {
        set.add(e.source);
      }
    }

    // 二阶邻居
    const firstLayer = Array.from(set);
    for (const n of firstLayer) {
      for (const e of edges) {
        if (e.source === n) {
          set.add(e.target);
        }
        if (e.target === n) {
          set.add(e.source);
        }
      }
    }
    return set;
  }, [edges, selectedNodeId]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = echarts.init(containerRef.current);

    const graphNodes = nodes.map((n) => {
      const inFocus = !selectedNodeId || neighbors.has(n.id);
      return {
        id: n.id,
        name: n.name,
        value: n.type,
        draggable: true,
        symbolSize: Math.max(26, Math.min(86, n.size)),
        itemStyle: {
          color: palette[n.type] || palette.Entity,
          opacity: inFocus ? 0.95 : 0.16,
          borderColor: selectedNodeId === n.id ? "#ffffff" : "rgba(255,255,255,0.35)",
          borderWidth: selectedNodeId === n.id ? 3 : 1.2,
          shadowColor: "rgba(0, 40, 80, 0.35)",
          shadowBlur: 14
        },
        label: {
          show: true,
          color: "#0f2747",
          fontSize: 12,
          fontWeight: 600
        },
        properties: n.properties
      };
    });

    const graphLinks = edges.map((e) => {
      const inFocus = !selectedNodeId || (neighbors.has(e.source) && neighbors.has(e.target));
      return {
        source: e.source,
        target: e.target,
        value: e.type,
        lineStyle: {
          color: inFocus ? "rgba(30, 98, 121, 0.55)" : "rgba(30, 98, 121, 0.07)",
          width: Math.max(1, e.weight * 2.2),
          opacity: 1,
          curveness: 0.15
        },
        label: {
          show: inFocus,
          formatter: EDGE_TYPE_ZH[e.type] || e.type,
          color: "#1f4b66",
          fontSize: 10
        },
        emphasis: {
          lineStyle: {
            width: Math.max(2.2, e.weight * 3)
          }
        }
      };
    });

    chart.setOption({
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(9, 28, 46, 0.93)",
        borderColor: "#1fa9c9",
        textStyle: { color: "#e9fbff" },
        formatter: (params: any) => {
          if (params.dataType === "edge") {
            const sourceId = String(params.data.source);
            const targetId = String(params.data.target);
            const sourceName = nodeNameMap.get(sourceId) || sourceId;
            const targetName = nodeNameMap.get(targetId) || targetId;
            return `关系：${EDGE_TYPE_ZH[params.data.value] || params.data.value}<br/>${sourceName} → ${targetName}`;
          }
          const p = params.data.properties || {};
          const rows = Object.keys(p)
            .slice(0, 6)
            .map((k) => `${k}: ${String(p[k])}`)
            .join("<br/>");
          return `<b>${params.data.name}</b><br/>类型：${NODE_TYPE_ZH[params.data.value] || params.data.value}<br/>${rows}`;
        }
      },
      animationDurationUpdate: 700,
      series: [
        {
          type: "graph",
          layout,
          roam: true,
          data: graphNodes,
          links: graphLinks,
          edgeSymbol: ["none", "arrow"],
          edgeSymbolSize: 7,
          force:
            layout === "force"
              ? {
                repulsion: 340,
                edgeLength: [120, 240],
                gravity: 0.08,
                friction: 0.22
              }
              : undefined,
          circular:
            layout === "circular"
              ? {
                rotateLabel: true
              }
              : undefined,
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 3
            }
          }
        }
      ]
    });

    const onClick = (params: any) => {
      if (params.dataType === "node") {
        const id = String(params.data.id);
        onNodeClick(id === selectedNodeId ? null : id);
      }
    };

    chart.on("click", onClick);

    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);

    return () => {
      chart.off("click", onClick);
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [edges, layout, neighbors, nodeNameMap, nodes, onNodeClick, selectedNodeId]);

  return <div ref={containerRef} className="h-[1200px] w-full xl:h-[1320px]" />;
}
