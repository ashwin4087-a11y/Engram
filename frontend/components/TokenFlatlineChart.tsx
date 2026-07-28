"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { TrendingDown, BarChart3, Zap, Clock } from "lucide-react";

/* ─── Types ─── */
interface TokenDataPoint {
  turn: number;
  tokenCount: number;
  latencyMs: number;
  memoriesUsed: number;
  timestamp: Date;
}

interface Props {
  sessionId: string | null;
  dataPoints: TokenDataPoint[];
}

/* ─── Mini sparkline (pure CSS + divs) ─── */
function Sparkline({ data, maxVal, color }: { data: number[]; maxVal: number; color: string }) {
  if (data.length === 0) return null;
  const barWidth = Math.max(4, Math.min(12, 200 / data.length));

  return (
    <div className="flex items-end gap-[2px] h-[48px]">
      {data.map((val, i) => {
        const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
        return (
          <div
            key={i}
            className="rounded-t-sm transition-all duration-500 ease-smooth"
            style={{
              width: `${barWidth}px`,
              height: `${Math.max(2, pct)}%`,
              background: i === data.length - 1
                ? color
                : `${color}60`,
              opacity: i === data.length - 1 ? 1 : 0.5 + (i / data.length) * 0.5,
            }}
          />
        );
      })}
    </div>
  );
}

/* ─── Metric card ─── */
function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  trend,
  trendLabel,
  accent,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  unit: string;
  trend?: "flat" | "up" | "down";
  trendLabel?: string;
  accent: string;
}) {
  const trendColors = {
    flat: "text-green-600 bg-green-50",
    up: "text-red-500 bg-red-50",
    down: "text-green-600 bg-green-50",
  };
  const trendIcons = {
    flat: "→",
    up: "↑",
    down: "↓",
  };

  return (
    <div className="flex flex-col gap-2 bg-white border border-border rounded-xl px-4 py-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: `${accent}15`, border: `1px solid ${accent}30` }}
          >
            <Icon size={13} style={{ color: accent }} />
          </div>
          <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
            {label}
          </span>
        </div>
        {trend && (
          <span
            className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md ${trendColors[trend]}`}
          >
            {trendIcons[trend]} {trendLabel}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold text-text-primary tracking-tight font-mono">
          {value}
        </span>
        <span className="text-[11px] text-text-secondary">{unit}</span>
      </div>
    </div>
  );
}

/* ─── Main chart panel ─── */
export default function TokenFlatlineChart({ sessionId, dataPoints }: Props) {
  const maxTokens = Math.max(2000, ...dataPoints.map((d) => d.tokenCount));
  const maxLatency = Math.max(100, ...dataPoints.map((d) => d.latencyMs));
  const tokenValues = dataPoints.map((d) => d.tokenCount);
  const latencyValues = dataPoints.map((d) => d.latencyMs);

  const latest = dataPoints[dataPoints.length - 1];
  const avgTokens =
    dataPoints.length > 0
      ? Math.round(dataPoints.reduce((s, d) => s + d.tokenCount, 0) / dataPoints.length)
      : 0;
  const avgLatency =
    dataPoints.length > 0
      ? Math.round(dataPoints.reduce((s, d) => s + d.latencyMs, 0) / dataPoints.length)
      : 0;

  // Calculate trend
  const getTokenTrend = (): "flat" | "up" | "down" => {
    if (dataPoints.length < 3) return "flat";
    const recent = dataPoints.slice(-3);
    const range = Math.max(...recent.map((d) => d.tokenCount)) - Math.min(...recent.map((d) => d.tokenCount));
    if (range < avgTokens * 0.15) return "flat";
    return recent[recent.length - 1].tokenCount > recent[0].tokenCount ? "up" : "down";
  };

  const isEmpty = dataPoints.length === 0;

  return (
    <div className="flex flex-col h-full bg-bg">
      {/* Header */}
      <div className="px-5 py-4 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-accent" />
          <h2 className="text-[13px] font-semibold text-text-primary tracking-tight">
            Token Budget & Performance
          </h2>
        </div>
        <p className="text-[11px] text-text-secondary mt-1 font-mono">
          Context token count stays flat as observations grow — that&apos;s the point.
        </p>
      </div>

      {isEmpty ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center animate-fade-in">
            <div className="w-11 h-11 rounded-2xl bg-bg-secondary border border-border flex items-center justify-center mx-auto mb-3">
              <TrendingDown size={18} className="text-text-secondary" strokeWidth={1.5} />
            </div>
            <p className="text-[13px] font-semibold text-text-primary">No data yet</p>
            <p className="text-[12px] text-text-secondary mt-1">
              Send some observations to see the flatline in action.
            </p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Metric cards */}
          <div className="grid grid-cols-2 gap-3">
            <MetricCard
              icon={Zap}
              label="Avg Tokens"
              value={avgTokens.toLocaleString()}
              unit="tokens/turn"
              trend={getTokenTrend()}
              trendLabel={getTokenTrend() === "flat" ? "Flat" : getTokenTrend() === "up" ? "+Growth" : "-Shrink"}
              accent="#2563EB"
            />
            <MetricCard
              icon={Clock}
              label="Avg Latency"
              value={avgLatency.toString()}
              unit="ms"
              accent="#8B5CF6"
            />
          </div>

          {/* Token chart */}
          <div className="bg-white border border-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
                Context Tokens / Turn
              </span>
              <span className="text-[11px] font-mono text-text-secondary">
                Budget: 1,500
              </span>
            </div>

            {/* Budget line + bars */}
            <div className="relative">
              {/* Budget reference line */}
              <div
                className="absolute left-0 right-0 border-t border-dashed border-red-300 z-10"
                style={{
                  bottom: `${(1500 / maxTokens) * 48}px`,
                }}
              />
              <Sparkline data={tokenValues} maxVal={maxTokens} color="#2563EB" />
            </div>

            <div className="flex items-center justify-between mt-2">
              <span className="text-[10px] text-text-secondary font-mono">Turn 1</span>
              <span className="text-[10px] text-text-secondary font-mono">
                Turn {dataPoints.length}
              </span>
            </div>
          </div>

          {/* Latency chart */}
          <div className="bg-white border border-border rounded-xl p-4">
            <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
              Compilation Latency / Turn
            </span>
            <div className="mt-3">
              <Sparkline data={latencyValues} maxVal={maxLatency} color="#8B5CF6" />
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-[10px] text-text-secondary font-mono">Turn 1</span>
              <span className="text-[10px] text-text-secondary font-mono">
                Turn {dataPoints.length}
              </span>
            </div>
          </div>

          {/* Turns table */}
          {dataPoints.length > 0 && (
            <div className="bg-white border border-border rounded-xl overflow-hidden">
              <div className="px-4 py-2.5 border-b border-border">
                <span className="text-[11px] text-text-secondary uppercase tracking-widest font-semibold">
                  Per-Turn Breakdown
                </span>
              </div>
              <div className="max-h-[200px] overflow-y-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="text-text-secondary text-left border-b border-border">
                      <th className="px-4 py-2 font-semibold">Turn</th>
                      <th className="px-4 py-2 font-semibold">Tokens</th>
                      <th className="px-4 py-2 font-semibold">Latency</th>
                      <th className="px-4 py-2 font-semibold">Memories</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dataPoints.map((dp, i) => (
                      <tr
                        key={i}
                        className="border-b border-border/50 last:border-0 hover:bg-bg-secondary/50 transition-colors"
                      >
                        <td className="px-4 py-2 font-mono text-text-primary">{dp.turn}</td>
                        <td className="px-4 py-2 font-mono text-accent font-semibold">
                          {dp.tokenCount.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 font-mono text-text-secondary">{dp.latencyMs}ms</td>
                        <td className="px-4 py-2 font-mono text-text-secondary">{dp.memoriesUsed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export type { TokenDataPoint };
