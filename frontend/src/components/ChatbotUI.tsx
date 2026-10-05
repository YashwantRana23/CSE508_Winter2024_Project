"use client";

import { useEffect, useRef, useState } from "react";
import { chat, getErrorMessage, isCancelled } from "@/lib/api";
import { describeQuestionUnderstanding, downloadResearchBrief } from "@/lib/research-brief";
import { SourceCard } from "@/components/SourceCard";
import type { AnswerMode, ChatResponse, HistoryMessage, QuestionClassification, RetrievalMethod, Source } from "@/types";

interface Message extends HistoryMessage {
  result?: ChatResponse;
  question?: string;
}

const modeLabel = { generated: "AI-generated answer", excerpts: "Document excerpts", no_evidence: "No supporting evidence" };

export function ChatbotUI({ domain, domainLabel, method, available, selectedSource, onSelect }: { domain: string; domainLabel: string; method: RetrievalMethod; available: boolean; selectedSource: Source | null; onSelect: (source: Source) => void }) {
  const [input, setInput] = useState("");
  const [answerMode, setAnswerMode] = useState<AnswerMode>("auto");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState<{ text: string; history: HistoryMessage[] } | null>(null);
  const controller = useRef<AbortController | null>(null);
  const latest = [...messages].reverse().find((message) => message.result);

  useEffect(() => () => controller.current?.abort(), []);

  async function send(text: string, retryHistory?: HistoryMessage[]) {
    if (!text || loading || !available) return;
    const history = retryHistory ?? messages.slice(-16).map(({ role, content }) => ({ role, content }));
    const request = new AbortController();
    controller.current?.abort();
    controller.current = request;
    if (!retryHistory) setMessages((previous) => [...previous, { role: "user", content: text }]);
    setInput("");
    setError("");
    setNotice("");
    setRetry(null);
    setLoading(true);
    try {
      const result = await chat(domain, text, history, method, answerMode, request.signal);
      if (controller.current !== request || request.signal.aborted) return;
      setMessages((previous) => [...previous, { role: "assistant", content: result.response, question: text, result }]);
    } catch (err) {
      if (controller.current !== request) return;
      if (!isCancelled(err)) {
        setError(getErrorMessage(err, "Could not complete your question. Please retry."));
        setRetry({ text, history });
      }
    } finally {
      if (controller.current === request) {
        controller.current = null;
        setLoading(false);
      }
    }
  }

  function cancel() {
    controller.current?.abort();
    controller.current = null;
    setLoading(false);
    setNotice("Request cancelled. You can ask another question.");
  }

  function clearConversation() {
    controller.current?.abort();
    controller.current = null;
    setMessages([]);
    setInput("");
    setLoading(false);
    setError("");
    setRetry(null);
    setNotice("");
  }

  function exportLatest() {
    if (!latest?.result) return;
    downloadResearchBrief({
      question: latest.question ?? "",
      domain: domainLabel,
      mode: modeLabel[latest.result.mode],
      retrievalMethod: latest.result.retrieval.method,
      retrievalWarning: latest.result.retrieval.warning,
      classification: latest.result.classification,
      response: latest.content,
      reason: latest.result.reason,
      sources: latest.result.sources,
    });
  }

  return (
    <section className="research-panel" aria-labelledby="assistant-heading">
      <div className="section-heading">
        <div><p className="eyebrow">Research assistant</p><h2 id="assistant-heading">Ask. Inspect. Verify.</h2></div>
        {messages.length > 0 && <button type="button" className="text-button" onClick={clearConversation}>Clear conversation</button>}
      </div>
      <div className="assistant-options">
        <label htmlFor="answer-mode">Answer mode</label>
        <select id="answer-mode" value={answerMode} disabled={loading} onChange={(event) => setAnswerMode(event.target.value as AnswerMode)}>
          <option value="auto">Auto · AI with excerpt fallback</option>
          <option value="excerpts">Document excerpts · no AI generation</option>
        </select>
      </div>
      <p className="helper-text">{answerMode === "auto" ? "Answers use retrieved passages. If generation is unavailable, the result is clearly labeled as document excerpts." : "Find and read original passages without an AI-generated interpretation."}</p>

      <div className="conversation" aria-live="polite" aria-relevant="additions" aria-busy={loading}>
        {messages.length === 0 && <div className="chat-empty"><span className="small-mark" aria-hidden="true">§</span><h3>A question is a starting point.</h3><p>Ask about the selected corpus. Every response keeps its source passages close by.</p><button type="button" className="suggestion" disabled={!available} onClick={() => setInput("What does Section 302 of the IPC say about punishment for murder?")}>Try: What does Section 302 say? <span aria-hidden="true">↗</span></button></div>}
        {messages.map((message, index) => (
          <article key={index} className={`chat-message ${message.role}`}>
            <div className="message-heading"><span>{message.role === "user" ? "You" : "Legal Lens"}</span>{message.result && <span className={`badge ${message.result.mode === "generated" ? "teal" : "amber"}`}>{modeLabel[message.result.mode]}</span>}</div>
            <p className="message-content">{message.content}</p>
            {message.result?.classification && <QuestionUnderstanding classification={message.result.classification} />}
            {message.result?.reason && <p className="mode-note">{message.result.reason}</p>}
            {message.result?.retrieval.warning && <p className="mode-note">{message.result.retrieval.warning}</p>}
            {!!message.result?.sources.length && <details className="answer-sources"><summary>Inspect {message.result.sources.length} source passages</summary><div className="source-list">{message.result.sources.map((source) => <SourceCard key={source.id} source={source} compact selected={source.id === selectedSource?.id} onSelect={onSelect} />)}</div></details>}
            {message.result && <p className="fineprint">{message.result.retrieval.warning?.startsWith("Retrieval skipped:") ? "Retrieval skipped" : `${message.result.retrieval.method === "hybrid" ? "Hybrid retrieval" : "Keyword retrieval"} · ${Math.round(message.result.retrieval.elapsed_ms)} ms retrieval`}</p>}
          </article>
        ))}
        {loading && <div className="loading-state" role="status"><span className="loading-dot" />Understanding your question, then finding evidence. Local models may take longer to load on the first request…</div>}
      </div>

      <form className="chat-compose" onSubmit={(event) => { event.preventDefault(); void send(input.trim()); }}>
        <label className="sr-only" htmlFor="legal-question">Ask a legal research question</label>
        <textarea id="legal-question" rows={3} maxLength={2000} disabled={!available || loading} value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a question about the historical IPC corpus…" />
        <div className="compose-actions"><span className="fineprint">Switching corpus or refreshing clears this conversation. Search-method changes apply to the next question.</span>{loading ? <button type="button" className="button secondary" onClick={cancel}>Cancel</button> : <button type="submit" className="button primary" disabled={!available || !input.trim()}>Ask assistant <span aria-hidden="true">↗</span></button>}</div>
      </form>
      {error && <div role="alert" className="error-notice">{error}{retry && <button type="button" className="text-button" disabled={loading} onClick={() => void send(retry.text, retry.history)}>Retry question</button>}</div>}
      {notice && <p role="status" className="helper-text">{notice}</p>}
      {latest?.result && <div className="brief-action"><div><strong>Keep the evidence.</strong><p>Download the latest answer, its question, scope, and source passages.</p></div><button type="button" className="button secondary" onClick={exportLatest}>Download brief ↓</button></div>}
    </section>
  );
}


function QuestionUnderstanding({ classification }: { classification: QuestionClassification }) {
  const understanding = describeQuestionUnderstanding(classification);
  const uncertain = classification.status === "unavailable" || classification.scope === "uncertain" || classification.intent === "uncertain";
  return (
    <details className="question-understanding">
      <summary>Question understanding <span className={`badge ${uncertain ? "amber" : "neutral"}`}>{classification.status === "unavailable" ? "Unavailable" : `${understanding.scope} · ${understanding.intent}`}</span></summary>
      <div className="question-understanding-body">
        <dl><div><dt>Scope</dt><dd>{understanding.scope}</dd></div><div><dt>Intent</dt><dd>{understanding.intent}</dd></div></dl>
        {classification.note && <p className={uncertain ? "mode-note" : "helper-text"}>{classification.note}</p>}
        <p className="fineprint">Local classifier · no API call for this step. This estimate is not a legal determination.{classification.model_version && ` Model: ${classification.model_version}.`}</p>
      </div>
    </details>
  );
}
