"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  AlertTriangle,
  ArrowRight,
  X,
} from "lucide-react";

/* ─── Types ─── */
interface Contradiction {
  id: string;
  entity_name: string;
  old_fact: string;
  new_fact: string;
  timestamp: Date;
  visible: boolean;
}

interface Props {
  contradictions: Contradiction[];
  onDismiss: (id: string) => void;
}

/* ─── Single Toast ─── */
function Toast({
  c,
  onDismiss,
}: {
  c: Contradiction;
  onDismiss: () => void;
}) {
  const [exiting, setExiting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setExiting(true);
      setTimeout(onDismiss, 300);
    }, 8000);
    return () => clearTimeout(timerRef.current);
  }, [onDismiss]);

  const dismiss = () => {
    setExiting(true);
    clearTimeout(timerRef.current);
    setTimeout(onDismiss, 300);
  };

  return (
    <div
      className={`group relative w-[360px] bg-white border border-red-200 rounded-2xl shadow-lg-soft overflow-hidden transition-all duration-300 ${
        exiting
          ? "opacity-0 translate-x-8 scale-95"
          : "opacity-100 translate-x-0 scale-100 animate-slide-up"
      }`}
    >
      {/* Top accent bar */}
      <div className="h-[3px] bg-gradient-to-r from-red-400 via-orange-400 to-amber-400" />

      <div className="px-4 py-3.5">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center shrink-0">
              <AlertTriangle size={14} className="text-red-500" />
            </div>
            <div>
              <p className="text-[12px] font-semibold text-text-primary leading-tight">
                Contradiction Detected
              </p>
              <p className="text-[11px] text-text-secondary font-mono mt-0.5">
                {c.entity_name}
              </p>
            </div>
          </div>
          <button
            onClick={dismiss}
            className="w-6 h-6 flex items-center justify-center rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors opacity-0 group-hover:opacity-100"
          >
            <X size={12} />
          </button>
        </div>

        {/* Contradiction details */}
        <div className="mt-3 flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <div className="w-1.5 h-1.5 rounded-full bg-red-300 shrink-0" />
              <span className="text-[10px] uppercase tracking-widest text-text-secondary font-semibold">
                Was
              </span>
            </div>
            <p className="text-[12px] text-text-secondary leading-relaxed line-clamp-2 pl-3">
              {c.old_fact}
            </p>
          </div>
          <ArrowRight
            size={12}
            className="text-text-secondary shrink-0 mt-3"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
              <span className="text-[10px] uppercase tracking-widest text-text-secondary font-semibold">
                Now
              </span>
            </div>
            <p className="text-[12px] text-text-primary leading-relaxed line-clamp-2 font-medium pl-3">
              {c.new_fact}
            </p>
          </div>
        </div>

        {/* Time */}
        <p className="text-[10px] text-text-secondary font-mono mt-2.5 text-right">
          {c.timestamp.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
          })}
        </p>
      </div>

      {/* Progress bar */}
      <div className="h-[2px] bg-red-50">
        <div
          className="h-full bg-red-300 rounded-full"
          style={{
            animation: "shrink 8s linear forwards",
          }}
        />
      </div>

      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
}

/* ─── Container ─── */
export default function ContradictionToast({ contradictions, onDismiss }: Props) {
  const visible = contradictions.filter((c) => c.visible);
  if (visible.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-3">
      {visible.slice(-5).map((c) => (
        <Toast key={c.id} c={c} onDismiss={() => onDismiss(c.id)} />
      ))}
    </div>
  );
}

export type { Contradiction };
