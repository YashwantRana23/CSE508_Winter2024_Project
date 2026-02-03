"use client";

import { useState, useRef, useEffect } from "react";
import { chat } from "@/lib/api";

const DOMAINS = [
  { id: "murder", label: "Murder Law" },
  { id: "child", label: "Child Law" },
  { id: "maternity", label: "Maternity Law" },
  { id: "ipc", label: "Indian Penal Code (General)" },
] as const;

type DomainId = (typeof DOMAINS)[number]["id"];

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatbotUI() {
  const [domain, setDomain] = useState<DomainId>("ipc");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await chat(domain, text, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || "Failed to get response";
      setError(msg);
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${msg}` }]);
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
            onClick={() => setDomain(d.id)}
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
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your legal question..."
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="submit"
                disabled={loading}
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
