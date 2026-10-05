import axios from "axios";
import type { AnswerMode, ChatResponse, GraphData, HistoryMessage, RetrievalMethod, SearchResponse } from "@/types";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000,
  headers: { "Content-Type": "application/json" },
});

export async function retrieve(query: string, domain: string, method: RetrievalMethod, signal?: AbortSignal): Promise<SearchResponse> {
  const { data } = await api.post("/search/retrieve", { query, domain, method, top_k: 6 }, { signal });
  return data;
}

export async function generateKnowledgeGraph(documents: { text: string; name: string }[], signal?: AbortSignal): Promise<GraphData> {
  const { data } = await api.post("/knowledge-graph/generate", { documents }, { signal });
  return data;
}

export async function chat(domain: string, message: string, history: HistoryMessage[], method: RetrievalMethod, answerMode: AnswerMode, signal?: AbortSignal): Promise<ChatResponse> {
  const { data } = await api.post(`/chatbot/${domain}`, { domain, message, history, method, answer_mode: answerMode }, { signal });
  return data;
}

export async function submitFeedback(message: string, subject?: string, email?: string) {
  const { data } = await api.post("/feedback/submit", { message, subject, email });
  return data;
}

export function isCancelled(error: unknown): boolean {
  return axios.isCancel(error);
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
    if (error.code === "ECONNABORTED") return "The request took too long. The local hybrid model may still be warming up. Choose BM25 · keywords in Search method, then retry.";
    if (!error.response) return "Cannot reach the backend. Check that the local server is running, then retry.";
  }
  return fallback;
}

export type ChatStatus = Record<string, { available: boolean; reason?: string | null; mode?: string }>;
export async function getChatStatus(signal?: AbortSignal): Promise<ChatStatus> {
  const { data } = await api.get("/chatbot/status", { signal, timeout: 20000 });
  return data;
}

// Only source links served by this application's API may be opened or exported.
export function sourceUrl(path: string): string | null {
  if (!path.startsWith("/sources/") || path.startsWith("//")) return null;
  try {
    const base = new URL(API_BASE_URL, typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
    const url = new URL(path, base);
    if (url.origin !== base.origin || !url.pathname.startsWith("/sources/")) return null;
    return url.href;
  } catch {
    return null;
  }
}
