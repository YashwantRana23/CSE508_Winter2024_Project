"use client";

import { useEffect, useRef, useState } from "react";
import { ChatbotUI } from "@/components/ChatbotUI";
import { KnowledgeGraphViz } from "@/components/KnowledgeGraphViz";
import { SourceCard, SourcePanel } from "@/components/SourceCard";
import { generateKnowledgeGraph, getChatStatus, getErrorMessage, isCancelled, retrieve, submitFeedback, type ChatStatus } from "@/lib/api";
import { downloadResearchBrief } from "@/lib/research-brief";
import type { GraphData, RetrievalMethod, SearchResponse, Source } from "@/types";

const domains = [
  { id: "ipc", label: "Indian Penal Code (IPC)" },
  { id: "murder", label: "Murder law" },
  { id: "child", label: "Child law" },
  { id: "maternity", label: "Maternity law" },
];

export default function DashboardPage() {
  const [domain, setDomain] = useState("ipc");
  const [method, setMethod] = useState<RetrievalMethod>("hybrid");
  const [tab, setTab] = useState<"search" | "assistant">("search");
  const [status, setStatus] = useState<ChatStatus>({});
  const [statusError, setStatusError] = useState("");
  const [statusLoading, setStatusLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<Source | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const statusRef = useRef<AbortController | null>(null);
  const available = status[domain]?.available === true;
  const domainLabel = domains.find((item) => item.id === domain)?.label ?? domain;

  async function checkStatus() {
    statusRef.current?.abort();
    const request = new AbortController();
    statusRef.current = request;
    setStatusLoading(true);
    setStatusError("");
    try {
      const nextStatus = await getChatStatus(request.signal);
      if (!request.signal.aborted) setStatus(nextStatus);
    } catch (error) {
      if (!isCancelled(error)) setStatusError(getErrorMessage(error, "Could not check corpus availability."));
    } finally {
      if (!request.signal.aborted) setStatusLoading(false);
    }
  }

  useEffect(() => {
    const request = new AbortController();
    statusRef.current = request;
    getChatStatus(request.signal).then((data) => { if (!request.signal.aborted) setStatus(data); }).catch((error) => { if (!isCancelled(error)) setStatusError(getErrorMessage(error, "Could not check corpus availability.")); }).finally(() => { if (!request.signal.aborted) setStatusLoading(false); });
    return () => { statusRef.current?.abort(); requestRef.current?.abort(); };
  }, []);

  function resetResearch() {
    requestRef.current?.abort();
    requestRef.current = null;
    setSearchLoading(false);
    setResult(null);
    setSelected(null);
    setSearchError("");
    setNotice("");
  }

  async function search(text: string) {
    if (!text.trim() || !available || searchLoading) return;
    requestRef.current?.abort();
    const request = new AbortController();
    requestRef.current = request;
    setQuery(text);
    setResult(null);
    setSelected(null);
    setSearchError("");
    setNotice("");
    setSearchLoading(true);
    try {
      const response = await retrieve(text.trim(), domain, method, request.signal);
      if (requestRef.current !== request || request.signal.aborted) return;
      setResult(response);
    } catch (error) {
      if (requestRef.current === request && !isCancelled(error)) setSearchError(getErrorMessage(error, "Search failed. Please retry."));
    } finally {
      if (requestRef.current === request) {
        requestRef.current = null;
        setSearchLoading(false);
      }
    }
  }

  function selectSource(source: Source) {
    setSelected(source);
    if (window.matchMedia("(max-width: 960px)").matches) requestAnimationFrame(() => document.getElementById("source-evidence")?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

  function downloadSearch() {
    if (!result) return;
    downloadResearchBrief({ question: result.query, domain: domainLabel, mode: "Search results — document excerpts", retrievalMethod: result.retrieval.method, sources: result.results });
  }

  return (
    <div className="workspace">
      <a className="skip-link" href="#research-workspace">Skip to research workspace</a>
      <header className="site-header">
        <a className="brand" href="/dashboard" aria-label="Legal Lens 2.0 home"><span className="brand-mark" aria-hidden="true">§</span><span>Legal Lens <small>2.0</small></span></a>
        <div className="header-meta"><span className="status-dot" aria-hidden="true" />Open research workspace</div>
      </header>
      <main className="page-shell">
        <section className="hero">
          <div><p className="eyebrow">Your evidence, in focus</p><h1>Legal research.<br /><em>With a source for every step.</em></h1><p className="hero-copy">Explore legal passages, ask grounded questions, and keep a research brief you can verify.</p></div>
          <div className="hero-note"><span className="badge amber">Historical IPC demo</span><p>Built for research and learning.</p><span>Original passages. Page-linked sources. Clear answer modes.</span></div>
        </section>

        <div className="scope-note"><span className="scope-symbol" aria-hidden="true">i</span><p><strong>Know the scope.</strong> This demo uses a bundled historical legal corpus. It does not establish current Indian law or cover all legal domains. Verify the applicable law and original documents; this is not legal advice.</p></div>

        <section className="workspace-controls" aria-label="Shared research settings">
          <div className="control-field"><label htmlFor="corpus">Research corpus</label><select id="corpus" value={domain} onChange={(event) => { resetResearch(); setDomain(event.target.value); }}>{domains.map((item) => <option key={item.id} value={item.id} disabled={item.id !== domain && status[item.id]?.available !== true}>{item.label}{status[item.id]?.available === false ? " · unavailable" : ""}</option>)}</select></div>
          <div className="control-field"><label htmlFor="retrieval">Search method</label><select id="retrieval" value={method} onChange={(event) => { resetResearch(); setMethod(event.target.value as RetrievalMethod); }}><option value="hybrid">Hybrid · keywords + meaning</option><option value="bm25">BM25 · keywords</option></select></div>
          <div className="controls-status"><span className={`badge ${available ? "teal" : "neutral"}`}>{statusLoading ? "Connecting…" : available ? "Corpus ready" : "Corpus unavailable"}</span><p>Shared by search and assistant</p></div>
        </section>

        {(statusError || (!statusLoading && !available)) && <div className="error-notice" role="alert"><span>{statusError || status[domain]?.reason || "The selected corpus is unavailable. Add its source documents before researching it."}</span><button type="button" className="text-button" disabled={statusLoading} onClick={() => void checkStatus()}>Check again</button></div>}

        <div className="workspace-grid" id="research-workspace">
          <div className="research-column">
            <div className="workspace-tabs" role="tablist" aria-label="Research tools">
              <button id="search-tab" type="button" role="tab" aria-selected={tab === "search"} aria-controls="search-panel" tabIndex={tab === "search" ? 0 : -1} onKeyDown={(event) => { if (event.key === "ArrowRight" || event.key === "ArrowLeft") { setTab("assistant"); document.getElementById("assistant-tab")?.focus(); } }} onClick={() => setTab("search")}>01 <span>Find sources</span></button>
              <button id="assistant-tab" type="button" role="tab" aria-selected={tab === "assistant"} aria-controls="assistant-panel" tabIndex={tab === "assistant" ? 0 : -1} onKeyDown={(event) => { if (event.key === "ArrowRight" || event.key === "ArrowLeft") { setTab("search"); document.getElementById("search-tab")?.focus(); } }} onClick={() => setTab("assistant")}>02 <span>Ask the assistant</span></button>
            </div>

            <div id="search-panel" role="tabpanel" aria-labelledby="search-tab" hidden={tab !== "search"}>
              <section className="research-panel">
                <div className="section-heading"><div><p className="eyebrow">Source discovery</p><h2>Start with the evidence.</h2></div></div>
                <form className="search-form" onSubmit={(event) => { event.preventDefault(); void search(query); }}><label htmlFor="search-query" className="sr-only">Search the legal corpus</label><input id="search-query" maxLength={2000} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="A question, a section, or a legal concept…" /><button type="submit" className="button primary" disabled={!available || searchLoading || !query.trim()}>{searchLoading ? "Searching…" : "Find sources"}<span aria-hidden="true">↗</span></button></form>
                <div className="query-suggestions"><span>Try a starting point:</span>{["Section 302 punishment for murder", "Right of private defence", "Criminal conspiracy"].map((example) => <button type="button" className="suggestion" key={example} disabled={!available || searchLoading} onClick={() => void search(example)}>{example}</button>)}</div>
                {searchLoading && <div className="loading-state" role="status"><span className="loading-dot" />{method === "hybrid" ? "Retrieving passages. The first hybrid request may take longer…" : "Retrieving relevant passages…"}<button type="button" className="text-button" onClick={() => { resetResearch(); setNotice("Search cancelled."); }}>Cancel</button></div>}
                {searchError && <div role="alert" className="error-notice">{searchError}<button type="button" className="text-button" onClick={() => void search(query)}>Retry search</button></div>}
                {notice && <p role="status" className="helper-text">{notice}</p>}

                {result ? (
                  <div className="search-results">
                    <div className="results-heading"><div><h3>{result.results.length ? `${result.results.length} source passages` : "No matching evidence"}</h3><p>For “{result.query}”</p></div><span className="badge neutral">{result.retrieval.method === "hybrid" ? "Hybrid" : "BM25"} · {Math.round(result.retrieval.elapsed_ms)} ms</span></div>
                    {result.retrieval.warning && <p className="mode-note">{result.retrieval.warning}</p>}
                    {result.results.length ? <><div className="source-list">{result.results.map((source) => <SourceCard source={source} selected={source.id === selected?.id} onSelect={selectSource} key={source.id} />)}</div><div className="brief-action"><div><strong>Take your research with you.</strong><p>Export this query, its passages, and original source links.</p></div><button type="button" className="button secondary" onClick={downloadSearch}>Download brief ↓</button></div><SimilarityExplorer key={result.query + result.results.map((source) => source.id).join()} sources={result.results} /></> : <p className="empty-copy">Try a specific term or IPC section. The corpus may not contain evidence for your question.</p>}
                  </div>
                ) : !searchLoading && !searchError && <div className="search-empty"><span className="empty-number" aria-hidden="true">01—06</span><h3>From a question to six source passages.</h3><p>Search combines exact terms with semantic similarity when the local model is available. Open any passage to check its original PDF page.</p></div>}
              </section>
            </div>
            <div id="assistant-panel" role="tabpanel" aria-labelledby="assistant-tab" hidden={tab !== "assistant"}><ChatbotUI key={domain} domain={domain} domainLabel={domainLabel} method={method} available={available} selectedSource={selected} onSelect={selectSource} /></div>
          </div>
          <SourcePanel source={selected} onClose={() => setSelected(null)} />
        </div>
        <FeedbackSection />
        <footer className="site-footer"><span>Legal Lens 2.0 <span aria-hidden="true">/</span> Research with provenance</span><span>Historical corpus · Current-law coverage unverified</span></footer>
      </main>
    </div>
  );
}

function SimilarityExplorer({ sources }: { sources: Source[] }) {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function generate() {
    if (loading) return;
    const request = new AbortController();
    controller.current = request;
    setLoading(true);
    setError("");
    try {
      const graph = await generateKnowledgeGraph(sources.map((source) => ({ text: source.excerpt, name: `${source.title} · p. ${source.page}` })), request.signal);
      if (!request.signal.aborted) setData(graph);
    } catch (err) {
      if (!isCancelled(err)) setError(getErrorMessage(err, "Could not create the similarity view."));
    } finally {
      if (!request.signal.aborted) setLoading(false);
    }
  }

  return <details className="similarity-section"><summary>Explore passage similarity <span>Optional</span></summary><p className="helper-text">A legacy TF-IDF view of text similarity between these excerpts. It does not represent legal relationships or re-rank results for your question.</p><button type="button" className="button secondary" onClick={() => void generate()} disabled={loading}>{loading ? "Building view…" : "Build similarity view"}</button>{error && <p role="alert" className="error-notice">{error}</p>}{data && <div className="graph-container"><KnowledgeGraphViz nodes={data.nodes} edges={data.edges} /></div>}</details>;
}

function FeedbackSection() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!message.trim() || loading) return;
    setLoading(true);
    setError("");
    try { await submitFeedback(message.trim(), "Legal Lens 2.0 workspace"); setSent(true); setMessage(""); }
    catch (err) { setError(getErrorMessage(err, "Could not submit feedback. Please retry.")); }
    finally { setLoading(false); }
  }

  return <details className="feedback-section"><summary>Help improve the research experience <span>Leave feedback ↗</span></summary>{sent ? <p role="status" className="success-notice">Thank you. Your feedback was saved.</p> : <form onSubmit={submit}><label htmlFor="feedback-message">What could work better?</label><textarea id="feedback-message" rows={3} maxLength={10000} value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Share an issue or a suggestion. Avoid including sensitive personal information." required />{error && <p role="alert" className="error-notice">{error}</p>}<button type="submit" className="button secondary" disabled={loading || !message.trim()}>{loading ? "Saving…" : "Submit feedback"}</button></form>}</details>;
}
