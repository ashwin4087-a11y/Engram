"use client";

import { useState } from "react";
import { Search, Loader2, Brain, FileText, Zap } from "lucide-react";

/* ─── Types ─── */
interface SupportingMemory {
  memory_type: string;
  content: string;
  score: number;
  entity_name?: string;
}

interface QueryResult {
  query: string;
  answer: string;
  supporting_memories: SupportingMemory[];
  retrieval_latency_ms: number;
}

interface Props {
  sessionId: string | null;
}

/* ─── Memory type styling ─── */
const TYPE_STYLES: Record<string, { bg: string; text: string }> = {
  fact:     { bg: "bg-blue-50",    text: "text-blue-700" },
  episode:  { bg: "bg-purple-50",  text: "text-purple-700" },
  entity:   { bg: "bg-amber-50",   text: "text-amber-700" },
};

/* ─── Main ─── */
export default function QueryConsole({ sessionId }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<QueryResult[]>([]);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    const text = query.trim();
    if (!text || !sessionId || loading) return;

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, query: text, max_results: 10 }),
      });
      const data = await res.json();
      setResults((prev) => [
        {
          query: text,
          answer: data.answer ?? "No answer generated.",
          supporting_memories: data.supporting_memories ?? [],
          retrieval_latency_ms: data.retrieval_latency_ms ?? 0,
        },
        ...prev,
      ]);
      setQuery("");
    } catch {
      setResults((prev) => [
        {
          query: text,
          answer: "Failed to reach the backend.",
          supporting_memories: [],
          retrieval_latency_ms: 0,
        },
        ...prev,
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Header */}
      <div className="px-5 py-4 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <Brain size={14} className="text-accent" />
          <h2 className="text-[13px] font-semibold text-text-primary tracking-tight">
            Ask the World Model
          </h2>
        </div>
        <p className="text-[11px] text-text-secondary mt-1 font-mono">
          Query the structured memory directly — bypasses the agent runtime.
        </p>
      </div>

      {/* Input */}
      <div className="px-5 py-3 border-b border-border bg-card shrink-0">
        <div
          className="flex items-center gap-2 bg-bg rounded-xl pl-4 pr-2 py-2"
          style={{
            boxShadow: "0 0 0 1px #E8E8E5, 0 1px 3px rgba(0,0,0,0.04)",
          }}
        >
          <Search size={14} className="text-text-secondary shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
            placeholder="e.g. What does Alice prefer?"
            disabled={!sessionId || loading}
            className="flex-1 bg-transparent text-[13px] text-text-primary placeholder-text-secondary outline-none font-sans disabled:opacity-40"
          />
          <button
            onClick={submit}
            disabled={!query.trim() || !sessionId || loading}
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-text-primary text-white hover:opacity-80 disabled:opacity-25 transition-all active:scale-95"
          >
            {loading ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <Search size={13} />
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto">
        {results.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center animate-fade-in">
              <div className="w-11 h-11 rounded-2xl bg-bg-secondary border border-border flex items-center justify-center mx-auto mb-3">
                <Brain size={18} className="text-text-secondary" strokeWidth={1.5} />
              </div>
              <p className="text-[13px] font-semibold text-text-primary">
                Query the world model
              </p>
              <p className="text-[12px] text-text-secondary mt-1 max-w-[200px] mx-auto">
                Ask questions about entities, facts, and relationships in memory.
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {results.map((r, i) => (
              <div
                key={i}
                className={`px-5 py-4 ${i === 0 ? "animate-slide-up" : ""}`}
              >
                {/* Query */}
                <div className="flex items-start gap-2 mb-3">
                  <div className="w-5 h-5 rounded-md bg-text-primary text-white flex items-center justify-center shrink-0 mt-0.5">
                    <Search size={10} />
                  </div>
                  <p className="text-[13px] font-medium text-text-primary">{r.query}</p>
                </div>

                {/* Answer */}
                <div className="ml-7 mb-3">
                  <div className="bg-white border border-border rounded-xl px-4 py-3">
                    <p className="text-[13px] text-text-primary leading-relaxed">
                      {r.answer}
                    </p>
                    {r.retrieval_latency_ms > 0 && (
                      <div className="flex items-center gap-1 mt-2">
                        <Zap size={10} className="text-text-secondary" />
                        <span className="text-[10px] font-mono text-text-secondary">
                          {r.retrieval_latency_ms}ms
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Supporting memories */}
                {r.supporting_memories.length > 0 && (
                  <div className="ml-7">
                    <div className="flex items-center gap-1.5 mb-2">
                      <FileText size={10} className="text-text-secondary" />
                      <span className="text-[10px] text-text-secondary uppercase tracking-widest font-semibold">
                        Supporting Evidence ({r.supporting_memories.length})
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {r.supporting_memories.map((m, j) => {
                        const style = TYPE_STYLES[m.memory_type] ?? TYPE_STYLES.fact;
                        return (
                          <div
                            key={j}
                            className="flex items-start gap-2 bg-bg-secondary/50 rounded-lg px-3 py-2"
                          >
                            <span
                              className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded shrink-0 mt-0.5 ${style.bg} ${style.text}`}
                            >
                              {m.memory_type}
                            </span>
                            <p className="text-[11px] text-text-primary leading-relaxed flex-1">
                              {m.content}
                            </p>
                            <span className="text-[10px] font-mono text-text-secondary shrink-0">
                              {m.score.toFixed(2)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
