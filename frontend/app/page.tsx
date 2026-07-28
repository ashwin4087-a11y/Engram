"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Moon,
  Network,
  MessageSquare,
  Activity,
  ChevronDown,
  BarChart3,
  History,
  Brain,
  AlertTriangle,
} from "lucide-react";
import { io, Socket } from "socket.io-client";
import ChatPanel from "@/components/ChatPanel";
import BrainGraph from "@/components/BrainGraph";
import ContradictionToast from "@/components/ContradictionToast";
import TokenFlatlineChart from "@/components/TokenFlatlineChart";
import ReplayScrubber from "@/components/ReplayScrubber";
import QueryConsole from "@/components/QueryConsole";
import type { Contradiction } from "@/components/ContradictionToast";
import type { TokenDataPoint } from "@/components/TokenFlatlineChart";

/* ─── Right-panel tab type ─── */
type RightTab = "graph" | "metrics" | "replay" | "query";

const RIGHT_TABS: { key: RightTab; label: string; icon: React.ElementType }[] = [
  { key: "graph",   label: "Graph",   icon: Network },
  { key: "metrics", label: "Metrics", icon: BarChart3 },
  { key: "replay",  label: "Replay",  icon: History },
  { key: "query",   label: "Query",   icon: Brain },
];

export default function Home() {
  const [sessionId, setSessionId]           = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [consolidating, setConsolidating]   = useState(false);
  const [activeTab, setActiveTab]           = useState<"chat" | "graph" | "activity">("chat");
  const [graphCollapsed, setGraphCollapsed] = useState(false);
  const [rightTab, setRightTab]             = useState<RightTab>("graph");

  // Contradiction toasts
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);

  // Token flatline data
  const [tokenData, setTokenData] = useState<TokenDataPoint[]>([]);
  const turnCountRef = useRef(0);

  // Timeline max turn
  const [maxTurn, setMaxTurn] = useState(0);

  // Socket.IO ref
  const socketRef = useRef<Socket | null>(null);

  /* ─── Create session on mount ─── */
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

  /* ─── Socket.IO connection ─── */
  useEffect(() => {
    if (!sessionId) return;

    const socket = io("http://localhost:8000", {
      transports: ["websocket", "polling"],
    });

    socket.on("connect", () => {
      socket.emit("join_session", { session_id: sessionId });
    });

    socket.on("engram_event", (data: any) => {
      const { type, payload } = data;

      // Contradiction events → show toast
      if (type === "contradiction.detected") {
        const newContradiction: Contradiction = {
          id: crypto.randomUUID(),
          entity_name: payload.entity_name ?? "Unknown",
          old_fact: payload.old_fact ?? "",
          new_fact: payload.new_fact ?? "",
          timestamp: new Date(),
          visible: true,
        };
        setContradictions((prev) => [...prev, newContradiction]);
      }

      // Context compiled → add token data point
      if (type === "context.compiled") {
        turnCountRef.current += 1;
        const dp: TokenDataPoint = {
          turn: turnCountRef.current,
          tokenCount: payload.token_count ?? 0,
          latencyMs: payload.latency_ms ?? 0,
          memoriesUsed: payload.memory_count ?? 0,
          timestamp: new Date(),
        };
        setTokenData((prev) => [...prev, dp]);
        setMaxTurn(turnCountRef.current);
      }

      // Graph updates → refresh
      if (
        type === "entity.created" ||
        type === "relationship.created" ||
        type === "consolidation.finished"
      ) {
        setRefreshTrigger((p) => p + 1);
      }
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [sessionId]);

  /* ─── Handlers ─── */
  const handleRefresh = () => setRefreshTrigger((p) => p + 1);

  const handleObserveComplete = useCallback(
    (data: any) => {
      // Track token data from observe responses even without socket events
      if (data?.context_bundle) {
        turnCountRef.current += 1;
        const dp: TokenDataPoint = {
          turn: turnCountRef.current,
          tokenCount: data.context_bundle.token_count ?? 0,
          latencyMs: data.context_bundle.compilation_latency_ms ?? 0,
          memoriesUsed: data.context_bundle.memories?.length ?? 0,
          timestamp: new Date(),
        };
        setTokenData((prev) => [...prev, dp]);
        setMaxTurn(turnCountRef.current);
      }
    },
    []
  );

  const consolidate = async () => {
    if (!sessionId || consolidating) return;
    setConsolidating(true);
    try {
      await fetch(
        `http://localhost:8000/api/v1/consolidate?session_id=${sessionId}`,
        { method: "POST" }
      );
      handleRefresh();
    } catch (e) {
      console.error("Consolidation failed:", e);
    } finally {
      setConsolidating(false);
    }
  };

  const dismissContradiction = (id: string) => {
    setContradictions((prev) =>
      prev.map((c) => (c.id === id ? { ...c, visible: false } : c))
    );
  };

  /* ─── Right-panel tab bar ─── */
  const TabBar = () => (
    <div className="flex items-center border-b border-border bg-card shrink-0">
      {RIGHT_TABS.map((tab) => {
        const active = rightTab === tab.key;
        const Icon = tab.icon;
        return (
          <button
            key={tab.key}
            onClick={() => setRightTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-widest transition-all border-b-2 ${
              active
                ? "text-accent border-accent"
                : "text-text-secondary border-transparent hover:text-text-primary hover:bg-bg-secondary/50"
            }`}
          >
            <Icon size={12} strokeWidth={2} />
            {tab.label}
          </button>
        );
      })}

      {/* Consolidate button in tab bar */}
      <div className="ml-auto pr-3">
        <button
          onClick={consolidate}
          disabled={!sessionId || consolidating}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-all duration-150 disabled:opacity-35"
        >
          <Moon
            size={12}
            className={consolidating ? "animate-spin" : ""}
            strokeWidth={2}
          />
          {consolidating ? "Consolidating…" : "Consolidate"}
        </button>
      </div>
    </div>
  );

  /* ─── Right-panel content ─── */
  const RightPanelContent = () => {
    switch (rightTab) {
      case "graph":
        return (
          <BrainGraph sessionId={sessionId} refreshTrigger={refreshTrigger} />
        );
      case "metrics":
        return (
          <TokenFlatlineChart sessionId={sessionId} dataPoints={tokenData} />
        );
      case "replay":
        return <ReplayScrubber sessionId={sessionId} maxTurn={maxTurn} />;
      case "query":
        return <QueryConsole sessionId={sessionId} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-bg overflow-hidden">

      {/* ── Top bar ─── */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          {/* Wordmark */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-text-primary flex items-center justify-center">
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

        {/* Right side status */}
        <div className="flex items-center gap-3">
          {/* Contradiction count badge */}
          {contradictions.filter((c) => c.visible).length > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-50 border border-red-100 animate-fade-in">
              <AlertTriangle size={11} className="text-red-500" />
              <span className="text-[11px] font-mono font-semibold text-red-600">
                {contradictions.filter((c) => c.visible).length}
              </span>
            </div>
          )}

          {/* Turn counter */}
          {maxTurn > 0 && (
            <span className="text-[11px] font-mono text-text-secondary">
              turn {maxTurn}
            </span>
          )}
        </div>
      </header>

      {/* ── Desktop layout (≥ 1024px): 30 / 70 split ─── */}
      <div className="hidden lg:flex flex-1 min-h-0">
        {/* Chat */}
        <div className="w-[30%] min-w-[300px] max-w-[440px] border-r border-border flex flex-col min-h-0">
          <ChatPanel sessionId={sessionId} onRefreshGraph={handleRefresh} />
        </div>
        {/* Right panel with tabs */}
        <div className="flex-1 flex flex-col min-h-0">
          <TabBar />
          <div className="flex-1 min-h-0">
            <RightPanelContent />
          </div>
        </div>
      </div>

      {/* ── Tablet layout (640px–1024px): stacked ─── */}
      <div className="hidden sm:flex lg:hidden flex-col flex-1 min-h-0">
        {/* Right panel tabs + content */}
        <div className="shrink-0">
          <TabBar />
        </div>
        {!graphCollapsed && (
          <div className="h-[40%] shrink-0 border-b border-border">
            <RightPanelContent />
          </div>
        )}
        <div className="flex-1 min-h-0">
          <ChatPanel sessionId={sessionId} onRefreshGraph={handleRefresh} />
        </div>
      </div>

      {/* ── Mobile layout (< 640px): tabs ─── */}
      <div className="flex sm:hidden flex-col flex-1 min-h-0">
        {/* Content */}
        <div className="flex-1 min-h-0">
          {activeTab === "chat"     && <ChatPanel  sessionId={sessionId} onRefreshGraph={handleRefresh} />}
          {activeTab === "graph"    && <BrainGraph sessionId={sessionId} refreshTrigger={refreshTrigger} />}
          {activeTab === "activity" && (
            <TokenFlatlineChart sessionId={sessionId} dataPoints={tokenData} />
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
            const labels = { chat: "Chat", graph: "Graph", activity: "Metrics" };
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
                {labels[tab]}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Contradiction toasts ─── */}
      <ContradictionToast
        contradictions={contradictions}
        onDismiss={dismissContradiction}
      />
    </div>
  );
}
