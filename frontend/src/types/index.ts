export type RetrievalMethod = "hybrid" | "bm25";
export type AnswerMode = "auto" | "excerpts";
export type ResponseMode = "generated" | "excerpts" | "no_evidence";

export interface Source {
  id: string;
  document_id: string;
  title: string;
  page: number;
  excerpt: string;
  url: string;
  corpus_status: "historical" | "unverified";
  score: number;
  rank: number;
}

export interface RetrievalInfo {
  method: string;
  elapsed_ms: number;
  warning?: string | null;
}

export interface SearchResponse {
  query: string;
  results: Source[];
  retrieval: RetrievalInfo;
  corpus_status: string | Record<string, unknown>;
}

export interface QuestionClassification {
  status: "ready" | "unavailable";
  model_version: string | null;
  scope: "historical" | "current" | "comparison" | "uncertain";
  intent: "section_lookup" | "explanation" | "comparison" | "unrelated" | "uncertain";
  note: string;
}

export interface ChatResponse {
  response: string;
  domain: string;
  mode: ResponseMode;
  reason: string | null;
  sources: Source[];
  retrieval: RetrievalInfo;
  request_id: string;
  classification?: QuestionClassification | null;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface GraphData {
  nodes: { id: string; label: string; rank: number; avg_similarity: number }[];
  edges: { source: string; target: string; weight: number }[];
  top_3: { rank: number; text: string; name: string }[];
}

export interface BM25ResultItem {
  text: string;
  name: string;
  score: number;
  rank: number;
}
