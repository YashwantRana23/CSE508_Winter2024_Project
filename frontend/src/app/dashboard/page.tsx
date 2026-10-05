"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { bm25Search, generateKnowledgeGraph, submitFeedback, api, getErrorMessage } from "@/lib/api";
import { KnowledgeGraphViz } from "@/components/KnowledgeGraphViz";
import { ChatbotUI } from "@/components/ChatbotUI";
import type { BM25ResultItem } from "@/types";

export default function DashboardPage() {
  const [corpusMode, setCorpusMode] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  useEffect(() => {
    api.get("/health").then(({ data }) => setCorpusMode(data.corpus_mode)).catch(() => setCorpusMode("offline"));
  }, []);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<BM25ResultItem[]>([]);
  const [kgData, setKgData] = useState<{
    nodes: { id: string; label: string; rank: number; avg_similarity: number }[];
    edges: { source: string; target: string; weight: number }[];
    top_3: { rank: number; text: string; name: string }[];
  } | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [processLoading, setProcessLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [processError, setProcessError] = useState("");

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || searchLoading || processLoading) return;
    setSearchError("");
    setProcessError("");
    setHasSearched(false);
    setSearchResults([]);
    setKgData(null);
    setSearchLoading(true);
    try {
      const res = await bm25Search(query.trim(), 10);
      setSearchResults(res.results || []);
      setHasSearched(true);
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Search failed");
      setSearchError(msg);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleProcess() {
    if (searchResults.length === 0 || processLoading || searchLoading) return;
    setProcessError("");
    setProcessLoading(true);
    try {
      const documents = searchResults.map((r) => ({ text: r.text, name: r.name }));
      const res = await generateKnowledgeGraph(documents);
      setKgData({
        nodes: res.nodes,
        edges: res.edges,
        top_3: res.top_3,
      });
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Failed to generate graph");
      setProcessError(msg);
    } finally {
      setProcessLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="text-xl font-bold text-indigo-600">
            Legal Lens
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
        {corpusMode === "demo" && (
          <p className="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-900">
            Demo corpus: 3 sample documents. Try “maternity benefit”, “murder”, or “child labour”. Configure DATA_PATH for your own CSV corpus.
          </p>
        )}
        {corpusMode === "offline" && <p role="alert" className="text-red-700">The backend is offline. Start it on port 8000, then refresh this page.</p>}
        {/* Search */}
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Legal Search (BM25)</h2>
          <form onSubmit={handleSearch} className="flex flex-col gap-4 sm:flex-row">
            <input
              type="text"
              aria-label="Legal search query"
              maxLength={2000}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your legal query..."
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={searchLoading || processLoading || !query.trim()}
              className="rounded-xl bg-indigo-600 px-6 py-2.5 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {searchLoading ? "Searching…" : "Search"}
            </button>
          </form>
          {searchError && (
            <p className="mt-2 text-sm text-red-600">{searchError}</p>
          )}

          {hasSearched && !searchLoading && searchResults.length === 0 && <p role="status" className="mt-4 text-slate-600">No matching documents found. Try different keywords.</p>}

          {searchResults.length > 0 && (
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-slate-600">Top {searchResults.length} results</p>
                <button
                  onClick={handleProcess}
                  disabled={processLoading || searchLoading}
                  className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
                >
                  {processLoading ? "Processing…" : "Process → Knowledge Graph"}
                </button>
              </div>
              {processError && (
                <p className="mb-2 text-sm text-red-600">{processError}</p>
              )}
              <ul className="max-h-64 space-y-2 overflow-y-auto rounded-lg border border-slate-200 p-3">
                {searchResults.map((r, i) => (
                  <li key={i} className="rounded bg-slate-50 p-2 text-sm">
                    <span className="font-medium text-slate-700">#{r.rank} {r.name}</span>
                    <p className="mt-1 line-clamp-2 text-slate-600">{r.text}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* Knowledge Graph + Top 3 */}
        {kgData && (
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">Knowledge Graph & Top 3</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="min-h-[400px] rounded-xl border border-slate-200 bg-slate-50">
                <KnowledgeGraphViz nodes={kgData.nodes} edges={kgData.edges} />
              </div>
              <div>
                <h3 className="mb-2 font-medium text-slate-700">Reranked top 3 results</h3>
                <ul className="space-y-3">
                  {kgData.top_3.map((r) => (
                    <li key={r.rank} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <span className="text-sm font-medium text-indigo-600">Rank {r.rank}: {r.name}</span>
                      <p className="mt-1 text-sm text-slate-600 line-clamp-4">{r.text}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        )}

        {/* Chatbot */}
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <ChatbotUI />
        </section>

        {/* Feedback */}
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <FeedbackSection />
        </section>
      </main>
    </div>
  );
}

function FeedbackSection() {
  const [message, setMessage] = useState("");
  const [subject, setSubject] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim() || loading) return;
    setError("");
    setLoading(true);
    try {
      await submitFeedback(message.trim(), subject || undefined, email || undefined);
      setSent(true);
      setMessage("");
      setSubject("");
      setEmail("");
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Failed to submit feedback"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h2 className="mb-4 text-lg font-semibold text-slate-800">Feedback</h2>
      {sent ? (
        <p className="rounded-lg bg-green-50 p-3 text-green-800">Thank you. Your feedback has been submitted.</p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Message *</label>
            <textarea
              aria-label="Feedback message"
              maxLength={10000}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
              rows={4}
              className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Your feedback or suggestion..."
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Subject</label>
              <input
                type="text"
                aria-label="Feedback subject"
                maxLength={200}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
              <input
                type="email"
                aria-label="Feedback email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Optional"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Submitting…" : "Submit feedback"}
          </button>
        </form>
      )}
    </>
  );
}
