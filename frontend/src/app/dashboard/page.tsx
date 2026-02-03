"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { bm25Search, generateKnowledgeGraph, chat, submitFeedback } from "@/lib/api";
import { KnowledgeGraphViz } from "@/components/KnowledgeGraphViz";
import { ChatbotUI } from "@/components/ChatbotUI";
import type { BM25ResultItem } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
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

  useEffect(() => {
    const token = localStorage.getItem("legal_lens_token");
    const u = localStorage.getItem("legal_lens_user");
    if (!token || !u) {
      router.replace("/login");
      return;
    }
    try {
      setUser(JSON.parse(u));
    } catch {
      router.replace("/login");
    }
  }, [router]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchError("");
    setKgData(null);
    setSearchLoading(true);
    try {
      const res = await bm25Search(query.trim(), 10);
      setSearchResults(res.results || []);
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || "Search failed";
      setSearchError(msg);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleProcess() {
    if (searchResults.length === 0) return;
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
      const msg = (err as { message?: string })?.message || "Failed to generate graph";
      setProcessError(msg);
    } finally {
      setProcessLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("legal_lens_token");
    localStorage.removeItem("legal_lens_user");
    router.replace("/login");
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="text-xl font-bold text-indigo-600">
            Legal Lens
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">{user.name}</span>
            <button
              onClick={handleLogout}
              className="rounded-lg bg-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-300"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
        {/* Search */}
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Legal Search (BM25)</h2>
          <form onSubmit={handleSearch} className="flex flex-col gap-4 sm:flex-row">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your legal query..."
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={searchLoading}
              className="rounded-xl bg-indigo-600 px-6 py-2.5 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {searchLoading ? "Searching…" : "Search"}
            </button>
          </form>
          {searchError && (
            <p className="mt-2 text-sm text-red-600">{searchError}</p>
          )}

          {searchResults.length > 0 && (
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-slate-600">Top {searchResults.length} results</p>
                <button
                  onClick={handleProcess}
                  disabled={processLoading}
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
    setError("");
    setLoading(true);
    try {
      await submitFeedback(message, subject || undefined, email || undefined);
      setSent(true);
      setMessage("");
      setSubject("");
      setEmail("");
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || "Failed to submit feedback");
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
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Optional"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Submitting…" : "Submit feedback"}
          </button>
        </form>
      )}
    </>
  );
}
