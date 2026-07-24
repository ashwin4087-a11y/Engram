"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowUp, Loader2, Database } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  entityCount?: number;
}

interface Props {
  sessionId: string | null;
  onRefreshGraph: () => void;
}

/* ─── Skeleton shimmer line ─── */
function SkeletonLine({ w }: { w: string }) {
  return (
    <div
      className="h-2.5 rounded-full skeleton"
      style={{ width: w }}
    />
  );
}

/* ─── Thinking bubble ─── */
function ThinkingBubble() {
  return (
    <div className="flex flex-col gap-1 items-start animate-fade-in">
      <span className="text-[11px] font-mono text-text-secondary px-0.5">
        {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
      </span>
      <div
        className="rounded-2xl rounded-bl-sm px-4 py-3.5 bg-card border border-border"
        style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
      >
        <div className="flex flex-col gap-1.5">
          <SkeletonLine w="120px" />
          <SkeletonLine w="88px" />
        </div>
      </div>
    </div>
  );
}

/* ─── Message bubble ─── */
function MessageBubble({ message, isLatest }: { message: Message; isLatest: boolean }) {
  const isUser = message.role === "user";
  const time = message.timestamp.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  return (
    <div
      className={`flex flex-col gap-1 ${isLatest ? "animate-slide-up" : ""} ${isUser ? "items-end" : "items-start"}`}
    >
      <span className="text-[11px] font-mono text-text-secondary px-0.5">{time}</span>

      <div
        className={`max-w-[82%] text-[14px] leading-relaxed px-4 py-3 rounded-2xl ${
          isUser
            ? "bg-text-primary text-white rounded-br-sm"
            : "bg-card text-text-primary rounded-bl-sm border border-border"
        }`}
        style={{
          boxShadow: isUser
            ? "0 2px 8px rgba(0,0,0,0.14), 0 1px 3px rgba(0,0,0,0.10)"
            : "0 1px 4px rgba(0,0,0,0.04)",
        }}
      >
        {message.content}
      </div>

      {!isUser && message.entityCount !== undefined && message.entityCount > 0 && (
        <div className="flex items-center gap-1.5 px-0.5 animate-fade-in">
          <Database size={10} className="text-text-secondary" />
          <span className="text-[11px] font-mono text-text-secondary">
            {message.entityCount} {message.entityCount === 1 ? "entity" : "entities"} recorded
          </span>
        </div>
      )}
    </div>
  );
}

/* ─── Empty state ─── */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 animate-fade-in text-center">
      <div
        className="w-11 h-11 rounded-2xl bg-bg-secondary border border-border flex items-center justify-center"
        style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.04)" }}
      >
        <Database size={18} className="text-text-secondary" strokeWidth={1.5} />
      </div>
      <div>
        <p className="text-[14px] font-semibold text-text-primary tracking-tight">No knowledge yet</p>
        <p className="text-[13px] text-text-secondary mt-1.5 max-w-[200px] leading-relaxed">
          Start a conversation and watch your world model evolve.
        </p>
      </div>
    </div>
  );
}

/* ─── Main ─── */
export default function ChatPanel({ sessionId, onRefreshGraph }: Props) {
  const [messages, setMessages]   = useState<Message[]>([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [focused, setFocused]     = useState(false);
  const bottomRef                 = useRef<HTMLDivElement>(null);
  const textareaRef               = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const resize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 128) + "px";
  };

  const send = async () => {
    const text = input.trim();
    if (!text || !sessionId || loading) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setLoading(true);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((p) => [...p, userMsg]);

    try {
      const res = await fetch("http://localhost:8000/api/v1/observe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text }),
      });
      const data = await res.json();

      setMessages((p) => [
        ...p,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply ?? "Memory recorded.",
          timestamp: new Date(),
          entityCount: data.compiler_result?.entities?.length ?? 0,
        },
      ]);
      onRefreshGraph();
    } catch {
      setMessages((p) => [
        ...p,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Unable to reach the backend. Please ensure the server is running.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const canSend = !!input.trim() && !!sessionId && !loading;

  return (
    <div className="flex flex-col h-full bg-card">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-6">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-5">
            {messages.map((msg, i) => (
              <MessageBubble key={msg.id} message={msg} isLatest={i === messages.length - 1} />
            ))}
            {loading && <ThinkingBubble />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="shrink-0 p-4 border-t border-border bg-card">
        <div
          className="flex items-end gap-2 bg-bg rounded-2xl pl-4 pr-2 py-2 transition-shadow duration-150"
          style={{
            boxShadow: focused
              ? "0 0 0 2px #2563EB"
              : "0 0 0 1px #E8E8E5, 0 1px 3px rgba(0,0,0,0.04)",
          }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => { setInput(e.target.value); resize(); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Ask anything…"
            disabled={!sessionId || loading}
            className="flex-1 resize-none bg-transparent text-[14px] text-text-primary placeholder-text-secondary outline-none leading-relaxed disabled:opacity-40 font-sans py-1"
            style={{ minHeight: "22px", maxHeight: "128px" }}
          />
          <button
            onClick={send}
            disabled={!canSend}
            className="shrink-0 mb-0.5 w-8 h-8 flex items-center justify-center rounded-xl bg-text-primary text-white hover:opacity-80 disabled:opacity-25 transition-all duration-150 active:scale-95"
            aria-label="Send message"
          >
            {loading
              ? <Loader2 size={14} className="animate-spin" />
              : <ArrowUp size={14} strokeWidth={2.5} />
            }
          </button>
        </div>
        <p className="text-[11px] text-text-secondary text-center mt-2 font-mono tracking-wide">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
