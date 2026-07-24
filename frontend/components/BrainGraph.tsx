"use client";

import { useEffect, useCallback, useState, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
} from "reactflow";
import type { Node, Edge, Connection } from "reactflow";
import "reactflow/dist/style.css";
import {
  User, MapPin, Lightbulb, CheckSquare, FolderOpen,
  Star, Package, Circle, Film, Hash,
} from "lucide-react";

/* ─── Type system ─── */
const ENTITY_ICONS: Record<string, React.ElementType> = {
  person:     User,
  location:   MapPin,
  concept:    Lightbulb,
  task:       CheckSquare,
  project:    FolderOpen,
  preference: Star,
  object:     Package,
  episode:    Film,
  default:    Hash,
};

const ENTITY_COLORS: Record<string, { bg: string; border: string; dot: string; icon: string }> = {
  person:     { bg: "#EFF6FF", border: "#BFDBFE", dot: "#3B82F6",  icon: "#3B82F6" },
  location:   { bg: "#F0FDF4", border: "#BBF7D0", dot: "#22C55E",  icon: "#22C55E" },
  concept:    { bg: "#FAFAF8", border: "#E0E0DC", dot: "#6B7280",  icon: "#6B7280" },
  task:       { bg: "#FFFBEB", border: "#FDE68A", dot: "#F59E0B",  icon: "#D97706" },
  project:    { bg: "#F5F3FF", border: "#DDD6FE", dot: "#8B5CF6",  icon: "#8B5CF6" },
  preference: { bg: "#FFF1F2", border: "#FECDD3", dot: "#F43F5E",  icon: "#F43F5E" },
  episode:    { bg: "#F0F9FF", border: "#BAE6FD", dot: "#0EA5E9",  icon: "#0EA5E9" },
  default:    { bg: "#FAFAF8", border: "#E8E8E5", dot: "#9CA3AF",  icon: "#9CA3AF" },
};

/* ─── Custom Node ─── */
function CustomNode({ data }: { data: any }) {
  const [hovered, setHovered] = useState(false);

  const isEpisode   = data.type === "episode";
  const isDecayed   = !!data.decayed;
  const isConsolidated = isEpisode && data.level > 0;

  const colors   = ENTITY_COLORS[data.type] ?? ENTITY_COLORS.default;
  const IconComp = ENTITY_ICONS[data.type]  ?? ENTITY_ICONS.default;

  const bg     = isConsolidated && !isDecayed ? "#ECFDF5" : colors.bg;
  const border = isConsolidated && !isDecayed ? "#6EE7B7" : colors.border;

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="relative"
      style={{ opacity: isDecayed ? 0.3 : 1, filter: isDecayed ? "grayscale(90%)" : "none" }}
    >
      {/* Hover tooltip */}
      {hovered && (
        <div
          className="absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full z-50 pointer-events-none animate-fade-scale-in"
          style={{ minWidth: "168px" }}
        >
          <div
            className="bg-white border border-border rounded-xl px-3.5 py-3"
            style={{ boxShadow: "0 8px 24px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06)" }}
          >
            {/* Type badge */}
            <div className="flex items-center gap-1.5 mb-2">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: colors.dot }} />
              <span className="text-[10px] font-semibold text-text-secondary uppercase tracking-widest">
                {data.type ?? "entity"}
              </span>
            </div>
            {/* Label */}
            <p className="text-[13px] font-semibold text-text-primary leading-snug">{data.label}</p>
            {/* Summary */}
            {data.fullSummary && (
              <p className="text-[11px] text-text-secondary mt-1.5 leading-relaxed line-clamp-3">
                {data.fullSummary}
              </p>
            )}
            {/* Status tags */}
            <div className="flex items-center gap-1.5 mt-2">
              {isDecayed && (
                <span className="text-[10px] font-mono text-text-secondary bg-bg-secondary px-1.5 py-0.5 rounded">
                  decayed
                </span>
              )}
              {isConsolidated && !isDecayed && (
                <span className="text-[10px] font-mono text-success bg-green-50 px-1.5 py-0.5 rounded">
                  consolidated
                </span>
              )}
            </div>
          </div>
          {/* Caret */}
          <div
            className="w-2.5 h-2.5 bg-white border-b border-r border-border rotate-45 mx-auto"
            style={{ marginTop: "-6px" }}
          />
        </div>
      )}

      {/* Node pill */}
      <div
        className="flex items-center gap-2 rounded-xl px-3.5 py-2.5 cursor-default select-none"
        style={{
          background: bg,
          border: `1.5px solid ${border}`,
          boxShadow: hovered
            ? "0 8px 24px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06)"
            : "0 2px 8px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.03)",
          transform: hovered ? "translateY(-2px)" : "translateY(0)",
          transition: "transform 180ms ease, box-shadow 180ms ease",
          minWidth: "100px",
          maxWidth: "200px",
        }}
      >
        <IconComp size={13} color={colors.icon} strokeWidth={2} className="shrink-0" />
        <span className="text-[13px] font-medium text-text-primary leading-none truncate">
          {data.label}
        </span>
        {isConsolidated && !isDecayed && (
          <div className="w-1.5 h-1.5 rounded-full bg-success shrink-0 animate-pulse-soft" />
        )}
      </div>
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

/* ─── Empty state ─── */
function EmptyGraph() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-5 pointer-events-none">
      {/* Placeholder network diagram — pure CSS */}
      <div className="relative w-24 h-24 animate-fade-in">
        <div className="absolute inset-0 rounded-full border border-border" />
        <div className="absolute w-3 h-3 rounded-full bg-border top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        {[0, 60, 120, 180, 240, 300].map((deg) => (
          <div
            key={deg}
            className="absolute w-2 h-2 rounded-full bg-border/60"
            style={{
              top: `${50 + 42 * Math.sin((deg * Math.PI) / 180)}%`,
              left: `${50 + 42 * Math.cos((deg * Math.PI) / 180)}%`,
              transform: "translate(-50%, -50%)",
            }}
          />
        ))}
      </div>
      <div className="text-center animate-slide-up">
        <p className="text-[15px] font-semibold text-text-primary tracking-tight">
          No knowledge graph yet
        </p>
        <p className="text-[13px] text-text-secondary mt-1.5 max-w-[220px] leading-relaxed">
          Start a conversation and watch your world model develop in real time.
        </p>
      </div>
    </div>
  );
}

/* ─── Stats bar ─── */
function StatsBar({ nodeCount, edgeCount }: { nodeCount: number; edgeCount: number }) {
  if (nodeCount === 0) return null;
  return (
    <div className="absolute top-3 right-3 z-10 flex items-center gap-3 bg-white/95 border border-border rounded-lg px-3 py-1.5 shadow-sm-soft animate-fade-in">
      <span className="text-[12px] font-mono text-text-primary font-medium">{nodeCount}</span>
      <span className="text-[10px] text-text-secondary uppercase tracking-widest">nodes</span>
      <div className="w-px h-3 bg-border" />
      <span className="text-[12px] font-mono text-text-primary font-medium">{edgeCount}</span>
      <span className="text-[10px] text-text-secondary uppercase tracking-widest">edges</span>
      <div className="w-px h-3 bg-border" />
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-success" />
        <span className="text-[10px] font-mono text-text-secondary">live</span>
      </div>
    </div>
  );
}

/* ─── Main ─── */
interface BrainGraphProps {
  sessionId: string | null;
  refreshTrigger: number;
}

export default function BrainGraph({ sessionId, refreshTrigger }: BrainGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [loading, setLoading] = useState(false);

  const fetchGraph = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res  = await fetch(`http://localhost:8000/api/v1/graph?session_id=${sessionId}`);
      const data = await res.json();
      const total = (data.nodes ?? []).length;

      const positioned: Node[] = (data.nodes ?? []).map((n: any, idx: number) => {
        const isEpisode = n.data?.type === "episode";
        const angle  = total > 1 ? (idx / total) * 2 * Math.PI : 0;
        const radius = isEpisode ? 300 : 170;

        return {
          ...n,
          type: "custom",
          position: {
            x: 480 + Math.cos(angle) * radius,
            y: 280 + Math.sin(angle) * radius,
          },
        };
      });

      setNodes(positioned);
      setEdges(
        (data.edges ?? []).map((e: any) => ({
          ...e,
          style: { stroke: "#D4D4D0", strokeWidth: 1.5 },
        }))
      );
    } catch (err) {
      console.error("Graph fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId, setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger, sessionId]);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((els) => addEdge(params, els)),
    [setEdges]
  );

  const isEmpty = nodes.length === 0 && !loading;

  return (
    <div className="relative w-full h-full" style={{ background: "#FAFAF8" }}>
      {isEmpty && <EmptyGraph />}
      <StatsBar nodeCount={nodes.length} edgeCount={edges.length} />

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3, maxZoom: 1.1 }}
        minZoom={0.15}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#E4E4E0" gap={28} size={1.2} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => (ENTITY_COLORS[n.data?.type] ?? ENTITY_COLORS.default).dot}
          maskColor="rgba(250,250,248,0.75)"
          style={{ borderRadius: 10 }}
        />
      </ReactFlow>

      {loading && nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center" style={{ background: "#FAFAF8" }}>
          <div className="flex flex-col items-center gap-3">
            <div className="w-6 h-6 rounded-full border-2 border-border border-t-accent animate-spin" />
            <span className="text-[11px] text-text-secondary font-mono tracking-wide">Fetching graph…</span>
          </div>
        </div>
      )}
    </div>
  );
}
