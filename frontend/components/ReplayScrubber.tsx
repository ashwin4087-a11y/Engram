"use client";

import { useState, useEffect, useCallback } from "react";
import { History, ChevronLeft, ChevronRight, Play, SkipBack, Eye, Hash } from "lucide-react";

/* ─── Types ─── */
interface ContextBundle {
  session_id: string;
  turn_number: number;
  token_count: number;
  token_budget: number;
  memories: Array<{
    memory_type: string;
    content: string;
    score: number;
    entity_name?: string;
  }>;
  context_text: string;
  compilation_latency_ms: number;
  created_at: string;
}

interface Props {
  sessionId: string | null;
  maxTurn: number;
}

/* ─── Memory type badges ─── */
const TYPE_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  fact:    { bg: "bg-blue-50",   text: "text-blue-700",   dot: "bg-blue-400" },
  episode: { bg: "bg-purple-50", text: "text-purple-700", dot: "bg-purple-400" },
  entity: { bg: "bg-amber-50",  text: "text-amber-700",  dot: "bg-amber-400" },
};

/* ─── Main ─── */
export default function ReplayScrubber({ sessionId, maxTurn }: Props) {
  const [currentTurn, setCurrentTurn] = useState(1);
  const [bundle, setBundle] = useState<ContextBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBundle = useCallback(
    async (turn: number) => {
      if (!sessionId || turn < 1) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `http://localhost:8000/api/v1/context-bundle/${turn}?session_id=${sessionId}`
        );
        if (!res.ok) {
          setBundle(null);
          setError(turn > maxTurn ? "No data for this turn yet" : "Bundle not found");
          return;
        }
        const data = await res.json();
        setBundle(data);
      } catch {
        setError("Failed to fetch bundle");
        setBundle(null);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, maxTurn]
  );

  useEffect(() => {
    if (sessionId && maxTurn > 0) {
      fetchBundle(currentTurn);
    }
  }, [currentTurn, sessionId, fetchBundle, maxTurn]);

  // Auto-play
  useEffect(() => {
    if (!playing || currentTurn >= maxTurn) {
      setPlaying(false);
      return;
    }
    const timer = setTimeout(() => setCurrentTurn((t) => t + 1), 1500);
    return () => clearTimeout(timer);
  }, [playing, currentTurn, maxTurn]);

  const prev = () => setCurrentTurn((t) => Math.max(1, t - 1));
  const next = () => setCurrentTurn((t) => Math.min(maxTurn, t + 1));
  const reset = () => {
    setCurrentTurn(1);
    setPlaying(false);
  };

  const isEmpty = maxTurn === 0;

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Header */}
      <div className="px-5 py-4 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <History size={14} className="text-accent" />
          <h2 className="text-[13px] font-semibold text-text-primary tracking-tight">
            Timeline Replay
          </h2>
        </div>
        <p className="text-[11px] text-text-secondary mt-1 font-mono">
          Scrub through context bundles to see exactly what the agent saw at each turn.
        </p>
      </div>

      {isEmpty ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center animate-fade-in">
            <div className="w-11 h-11 rounded-2xl bg-bg-secondary border border-border flex items-center justify-center mx-auto mb-3">
              <History size={18} className="text-text-secondary" strokeWidth={1.5} />
            </div>
            <p className="text-[13px] font-semibold text-text-primary">No turns recorded</p>
            <p className="text-[12px] text-text-secondary mt-1">
              Observe some data first, then replay here.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Scrubber controls */}
          <div className="px-5 py-3 border-b border-border bg-card shrink-0">
            <div className="flex items-center gap-3">
              {/* Reset */}
              <button
                onClick={reset}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors"
                title="Reset to turn 1"
              >
                <SkipBack size={14} />
              </button>

              {/* Previous */}
              <button
                onClick={prev}
                disabled={currentTurn <= 1}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors disabled:opacity-30"
              >
                <ChevronLeft size={16} />
              </button>

              {/* Slider */}
              <div className="flex-1 relative">
                <input
                  type="range"
                  min={1}
                  max={Math.max(1, maxTurn)}
                  value={currentTurn}
                  onChange={(e) => {
                    setPlaying(false);
                    setCurrentTurn(Number(e.target.value));
                  }}
                  className="w-full h-1.5 bg-bg-secondary rounded-full appearance-none cursor-pointer accent-accent"
                  style={{
                    background: `linear-gradient(to right, #2563EB 0%, #2563EB ${
                      ((currentTurn - 1) / Math.max(1, maxTurn - 1)) * 100
                    }%, #E8E8E5 ${((currentTurn - 1) / Math.max(1, maxTurn - 1)) * 100}%, #E8E8E5 100%)`,
                  }}
                />
              </div>

              {/* Next */}
              <button
                onClick={next}
                disabled={currentTurn >= maxTurn}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors disabled:opacity-30"
              >
                <ChevronRight size={16} />
              </button>

              {/* Play */}
              <button
                onClick={() => setPlaying(!playing)}
                disabled={currentTurn >= maxTurn}
                className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors disabled:opacity-30 ${
                  playing
                    ? "bg-accent text-white"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-secondary"
                }`}
                title={playing ? "Pause" : "Auto-play"}
              >
                <Play size={14} fill={playing ? "currentColor" : "none"} />
              </button>

              {/* Turn indicator */}
              <div className="flex items-center gap-1 text-[12px] font-mono text-text-primary bg-bg-secondary rounded-lg px-2.5 py-1.5 min-w-[72px] justify-center">
                <Hash size={10} className="text-text-secondary" />
                <span className="font-semibold">{currentTurn}</span>
                <span className="text-text-secondary">/ {maxTurn}</span>
              </div>
            </div>
          </div>

          {/* Bundle content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-5 h-5 rounded-full border-2 border-border border-t-accent animate-spin" />
              </div>
            ) : error ? (
              <div className="text-center py-12 text-[13px] text-text-secondary animate-fade-in">
                {error}
              </div>
            ) : bundle ? (
              <>
                {/* Stats row */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white border border-border rounded-xl px-4 py-3">
                    <span className="text-[10px] text-text-secondary uppercase tracking-widest font-semibold">
                      Tokens
                    </span>
                    <p className="text-lg font-semibold font-mono text-accent mt-0.5">
                      {bundle.token_count.toLocaleString()}
                      <span className="text-[11px] text-text-secondary font-normal">
                        {" "}/ {bundle.token_budget.toLocaleString()}
                      </span>
                    </p>
                  </div>
                  <div className="bg-white border border-border rounded-xl px-4 py-3">
                    <span className="text-[10px] text-text-secondary uppercase tracking-widest font-semibold">
                      Memories
                    </span>
                    <p className="text-lg font-semibold font-mono text-text-primary mt-0.5">
                      {bundle.memories.length}
                    </p>
                  </div>
                  <div className="bg-white border border-border rounded-xl px-4 py-3">
                    <span className="text-[10px] text-text-secondary uppercase tracking-widest font-semibold">
                      Latency
                    </span>
                    <p className="text-lg font-semibold font-mono text-text-primary mt-0.5">
                      {bundle.compilation_latency_ms}
                      <span className="text-[11px] text-text-secondary font-normal">ms</span>
                    </p>
                  </div>
                </div>

                {/* Memories list */}
                <div className="bg-white border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-border flex items-center gap-2">
                    <Eye size={12} className="text-text-secondary" />
                    <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
                      Retrieved Memories
                    </span>
                  </div>
                  <div className="divide-y divide-border/50">
                    {bundle.memories.map((m, i) => {
                      const colors = TYPE_COLORS[m.memory_type] ?? TYPE_COLORS.fact;
                      return (
                        <div key={i} className="px-4 py-3 hover:bg-bg-secondary/30 transition-colors">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span
                              className={`text-[10px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}
                            >
                              {m.memory_type}
                            </span>
                            {m.entity_name && (
                              <span className="text-[10px] font-mono text-text-secondary">
                                {m.entity_name}
                              </span>
                            )}
                            <span className="ml-auto text-[10px] font-mono text-text-secondary">
                              score: {m.score.toFixed(3)}
                            </span>
                          </div>
                          <p className="text-[12px] text-text-primary leading-relaxed">
                            {m.content}
                          </p>
                        </div>
                      );
                    })}
                    {bundle.memories.length === 0 && (
                      <div className="px-4 py-6 text-center text-[12px] text-text-secondary">
                        No memories in this bundle.
                      </div>
                    )}
                  </div>
                </div>

                {/* Raw context text */}
                <div className="bg-white border border-border rounded-xl overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-border">
                    <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
                      Compiled Context (what the LLM sees)
                    </span>
                  </div>
                  <pre className="px-4 py-3 text-[11px] font-mono text-text-primary leading-relaxed whitespace-pre-wrap max-h-[200px] overflow-y-auto bg-bg-secondary/30">
                    {bundle.context_text || "Empty context."}
                  </pre>
                </div>
              </>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
