export interface GraphNode {
  id: string;
  name: string;
  type: string;
  size: number;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  weight: number;
  evidence?: string;
}

export interface GraphMeta {
  total_nodes: number;
  total_edges: number;
  node_type_stats: Record<string, number>;
  edge_type_stats: Record<string, number>;
}

export interface GraphResponse {
  data: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  meta: GraphMeta;
}

export interface FingerprintSummary {
  morgan_on_bits: number;
  maccs_on_bits: number;
  morgan_on_indices_preview: number[];
  maccs_on_indices_preview: number[];
}

export interface MoleculeProfile {
  name: string;
  smiles: string;
  molecular_formula: string;
  descriptors: Record<string, string | number>;
  fingerprint: FingerprintSummary;
}

export interface GNNPrediction {
  node_id: string;
  node_name: string;
  node_type: string;
  score: number;
  explanation: string;
}

export interface IntegratedSearchResponse {
  keyword: string;
  kg: GraphResponse;
  molecules: MoleculeProfile[];
  gnn: {
    model_name: string;
    top_k: number;
    predictions: GNNPrediction[];
  };
  notes: string[];
}

export interface TemplateSummary {
  id: string;
  title: string;
  description: string;
}

export interface TemplateListResponse {
  templates: TemplateSummary[];
}

export interface TemplateDetailResponse {
  id: string;
  title: string;
  description: string;
  relation_legend: Record<string, string>;
  graph: GraphResponse;
}
