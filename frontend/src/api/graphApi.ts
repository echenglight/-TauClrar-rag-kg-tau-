import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import type {
  GraphResponse,
  IntegratedSearchResponse,
  TemplateDetailResponse,
  TemplateListResponse
} from "../types/graph";

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const baseUrlCandidates = [
  configuredBaseUrl,
  "http://127.0.0.1:8000",
  "http://localhost:8000"
].filter((url, index, arr): url is string => Boolean(url) && arr.indexOf(url) === index);

const api = axios.create({
  baseURL: baseUrlCandidates[0],
  timeout: 12000
});

function isNetworkError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}

async function requestWithFallback<T>(config: AxiosRequestConfig): Promise<T> {
  let lastError: unknown;

  for (const baseURL of baseUrlCandidates) {
    try {
      const { data } = await api.request<T>({ ...config, baseURL });
      return data;
    } catch (error) {
      lastError = error;
      if (!isNetworkError(error)) {
        break;
      }
    }
  }

  throw lastError;
}

export async function fetchGraphAll(): Promise<GraphResponse> {
  const data = await requestWithFallback<GraphResponse>({
    url: "/api/graph/all",
    method: "GET"
  });
  return data;
}

export async function searchGraph(keyword: string): Promise<GraphResponse> {
  const data = await requestWithFallback<GraphResponse>({
    url: "/api/graph/search",
    method: "GET",
    params: { keyword }
  });
  return data;
}

export async function searchIntegrated(keyword: string): Promise<IntegratedSearchResponse> {
  const data = await requestWithFallback<IntegratedSearchResponse>({
    url: "/api/analysis/search",
    method: "GET",
    params: { keyword, graph_limit: 400, molecule_limit: 5, gnn_top_k: 5 }
  });
  return data;
}

export async function fetchTemplateList(): Promise<TemplateListResponse> {
  const data = await requestWithFallback<TemplateListResponse>({
    url: "/api/templates",
    method: "GET"
  });
  return data;
}

export async function fetchTemplateDetail(templateId: string): Promise<TemplateDetailResponse> {
  const data = await requestWithFallback<TemplateDetailResponse>({
    url: `/api/templates/${templateId}`,
    method: "GET"
  });
  return data;
}

export interface ChatPayload {
  question: string;
  session_id?: string;
  top_k?: number;
  temperature?: number;
  source?: "dify" | "local_llm";
}

export async function chatWithAssistant(payload: ChatPayload): Promise<string> {
  try {
    const { data } = await api.post<{ answer: string }>("/api/chat/ask", payload);
    return data.answer;
  } catch {
    // 预留：后续可对接 Dify 或本地 LLM。
    const answer = [
      "### TauClear 智能助手（本地回退）",
      `你问的是：${payload.question}`,
      "",
      "已完成工作流占位：",
      "- 实体识别（Mock）",
      "- 图谱检索（Mock）",
      "- 证据聚合（Mock）",
      "",
      "建议下一步：将此请求替换为 Dify API 网关，并把 Neo4j 查询结果作为上下文注入。"
    ].join("\n");

    return new Promise((resolve) => {
      setTimeout(() => resolve(answer), 500);
    });
  }
}
