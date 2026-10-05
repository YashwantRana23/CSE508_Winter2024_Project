/**
 * API client for Legal Lens backend.
 * Base URL from env NEXT_PUBLIC_API_URL (default http://localhost:8000).
 */

import axios from "axios";

const baseURL =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Search
export async function bm25Search(query: string, topK = 10) {
  const { data } = await api.post("/search/bm25", { query, top_k: topK });
  return data;
}

// Knowledge graph
export async function generateKnowledgeGraph(documents: { text: string; name: string }[]) {
  const { data } = await api.post("/knowledge-graph/generate", { documents });
  return data;
}

// Rerank
export async function rerankCosine(documents: { text: string; name: string }[]) {
  const { data } = await api.post("/rerank/cosine", { documents });
  return data;
}

// Chatbot
export async function chat(domain: string, message: string, history?: { role: string; content: string }[]) {
  const { data } = await api.post(`/chatbot/${domain}`, { domain, message, history });
  return data;
}

// Feedback
export async function submitFeedback(message: string, subject?: string, email?: string) {
  const { data } = await api.post("/feedback/submit", { message, subject, email });
  return data;
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join("; ");
    if (!error.response) return "Cannot reach the server. Make sure the backend is running on port 8000.";
  }
  return fallback;
}

export type ChatStatus = Record<string, { available: boolean; reason: string }>;
export async function getChatStatus(): Promise<ChatStatus> {
  const { data } = await api.get("/chatbot/status");
  return data;
}
