"use client";

import { useEffect, useState } from "react";
import { Moon, Network, MessageSquare, Activity, ChevronDown } from "lucide-react";
import ChatPanel from "@/components/ChatPanel";
import BrainGraph from "@/components/BrainGraph";

export default function Home() {
  const [sessionId, setSessionId]         = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [consolidating, setConsolidating] = useState(false);
  const [activeTab, setActiveTab]         = useState<"chat" | "graph" | "activity">("chat");
  const [graphCollapsed, setGraphCollapsed] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res  = await fetch("http://localhost:8000/api/v1/sessions", { method: "POST" });
        const data = await res.json();
        setSessionId(data.id);
      } catch (e) {
        console.error("Backend unreachable:", e);
      }
    })();
  }, []);

  const handleRefresh = () => setRefreshTrigger((p) => p + 1);

  const consolidate = async () => {
    if (!sessionId || consolidating) return;
    setConsolidating(true);
    try {
      await fetch(`http://localhost:8000/api/v1/consolidate?session_id=${sessionId}`, { method: "POST" });
      handleRefresh();
    } catch (e) {
      console.error("Consolidation failed:", e);
    } finally {
      setConsolidating(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-bg overflow-hidden">

      {/* ── Top bar ─────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          {/* Wordmark */}
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded-md bg-text-primary flex items-center justify-center"
            >
              <span className="text-[10px] font-bold text-white tracking-tighter">E</span>
            </div>
            <span className="font-semibold text-[14px] text-text-primary tracking-tight">
              Engram
            </span>
          </div>

          {/* Separator */}
          <div className="w-px h-4 bg-border" />

          {/* Session ID */}
          <span className="text-[11px] font-mono text-text-secondary">
            {sessionId ? `session · ${sessionId.slice(0, 8)}` : "connecting…"}
          </span>
        </div>

        {/* Consolidate action */}
        <button
          onClick={consolidate}
          disabled={!sessionId || consolidating}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-all duration-150 disabled:opacity-35"
        >
          <Moon size={13} className={consolidating ? "animate-spin" : ""} strokeWidth={2} />
          {consolidating ? "Consolidating…" : "Consolidate Memory"}
        </button>
      </header>

      {/* ── Desktop layout (≥ 1024px): 30 / 70 split ───────── */}
      <div className="hidden lg:flex flex-1 min-h-0">
        {/* Chat */}
        <div className="w-[30%] min-w-[300px] max-w-[440px] border-r border-border flex flex-col min-h-0">
          <ChatPanel sessionId={sessionId} onRefreshGraph={handleRefresh} />
        </div>
        {/* Graph */}
        <div className="flex-1 min-h-0">
          <BrainGraph sessionId={sessionId} refreshTrigger={refreshTrigger} />
        </div>
      </div>

      {/* ── Tablet layout (640px–1024px): stacked ───────────── */}
      <div className="hidden sm:flex lg:hidden flex-col flex-1 min-h-0">
        {/* Graph collapse bar */}
        <button
          onClick={() => setGraphCollapsed((v) => !v)}
          className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card text-[12px] font-medium text-text-secondary hover:text-text-primary transition-colors shrink-0"
        >
          <span className="flex items-center gap-2 uppercase tracking-widest text-[10px]">
            <Network size={12} strokeWidth={2} />
            Knowledge Graph
          </span>
          <ChevronDown
            size={13}
            className={`transition-transform duration-200 ${graphCollapsed ? "-rotate-90" : ""}`}
          />
        </button>
        {!graphCollapsed && (
          <div className="h-[40%] shrink-0 border-b border-border">
            <BrainGraph sessionId={sessionId} refreshTrigger={refreshTrigger} />
          </div>
        )}
        <div className="flex-1 min-h-0">
          <ChatPanel sessionId={sessionId} onRefreshGraph={handleRefresh} />
        </div>
      </div>

      {/* ── Mobile layout (< 640px): tabs ───────────────────── */}
      <div className="flex sm:hidden flex-col flex-1 min-h-0">
        {/* Content */}
        <div className="flex-1 min-h-0">
          {activeTab === "chat"    && <ChatPanel  sessionId={sessionId} onRefreshGraph={handleRefresh} />}
          {activeTab === "graph"   && <BrainGraph sessionId={sessionId} refreshTrigger={refreshTrigger} />}
          {activeTab === "activity" && (
            <div className="flex items-center justify-center h-full text-[13px] text-text-secondary">
              Activity feed coming soon.
            </div>
          )}
        </div>
        {/* Bottom tab bar */}
        <div className="shrink-0 flex border-t border-border bg-card">
          {(["chat", "graph", "activity"] as const).map((tab) => {
            const icons = {
              chat:     <MessageSquare size={18} strokeWidth={1.8} />,
              graph:    <Network       size={18} strokeWidth={1.8} />,
              activity: <Activity      size={18} strokeWidth={1.8} />,
            };
            const active = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 flex flex-col items-center py-3 gap-1 text-[10px] font-medium uppercase tracking-widest transition-colors ${
                  active ? "text-accent" : "text-text-secondary"
                }`}
              >
                {icons[tab]}
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
