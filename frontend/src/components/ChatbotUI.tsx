"use client";

import { useState, useRef, useEffect } from "react";
import { chat, getChatStatus, getErrorMessage, type ChatStatus } from "@/lib/api";

const DOMAINS = [
  { id: "murder", label: "Murder Law" },
  { id: "child", label: "Child Law" },
  { id: "maternity", label: "Maternity Law" },
  { id: "ipc", label: "Indian Penal Code (General)" },
] as const;

type DomainId = (typeof DOMAINS)[number]["id"];

const EMPTY_MESSAGES: Message[] = [];

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatbotUI() {
  const [domain, setDomain] = useState<DomainId>("ipc");
  const [input, setInput] = useState("");
  const [conversations, setConversations] = useState<Partial<Record<DomainId, Message[]>>>({});
  const messages = conversations[domain] ?? EMPTY_MESSAGES;
  const [status, setStatus] = useState<ChatStatus>({});
  const [statusError, setStatusError] = useState("");
  const available = status[domain]?.available === true;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getChatStatus().then(setStatus).catch((err) => setStatusError(getErrorMessage(err, "Could not check chatbot availability.")));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || !available) return;
    const requestDomain = domain;
    function appendMessage(message: Message) {
      setConversations((prev) => ({ ...prev, [requestDomain]: [...(prev[requestDomain] ?? []), message] }));
    }
    setInput("");
    setError("");
    appendMessage({ role: "user", content: text });
    setLoading(true);
    try {
      const history = messages.slice(-40).map((m) => ({ role: m.role, content: m.content }));
      const res = await chat(domain, text, history);
      appendMessage({ role: "assistant", content: res.response });
    } catch (err: unknown) {
      const msg = getErrorMessage(err, "Failed to get response");
      setError(msg);

    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-slate-800">Domain-specific Chatbot</h2>
      <div className="mb-4 flex flex-wrap gap-2">
        {DOMAINS.map((d) => (
          <button
            key={d.id}
            disabled={loading}
            onClick={() => { setDomain(d.id); setError(""); }}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              domain === d.id
                ? "bg-indigo-600 text-white"
                : "bg-slate-200 text-slate-700 hover:bg-slate-300"
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>
      {!available && (
        <p role="status" className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
          {statusError || status[domain]?.reason || "Checking assistant availability…"}
        </p>
      )}
      <div className="rounded-xl border border-slate-200 bg-slate-50">
        <div className="flex h-[360px] flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <p className="text-center text-slate-500">
                Ask a question about {DOMAINS.find((d) => d.id === domain)?.label}. The assistant uses the selected legal domain.
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-white text-slate-800 shadow border border-slate-200"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-white px-4 py-2 shadow border border-slate-200">
                  <span className="text-sm text-slate-500">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form onSubmit={handleSend} className="border-t border-slate-200 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                aria-label="Legal question"
                disabled={!available || loading}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your legal question..."
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="submit"
                disabled={loading || !available || !input.trim()}
                className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Send
              </button>
            </div>
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </form>
        </div>
      </div>
    </div>
  );
}
