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

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("legal_lens_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export async function register(name: string, email: string, password: string) {
  const { data } = await api.post("/auth/register", { name, email, password });
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

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
