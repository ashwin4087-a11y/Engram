# Engram — The Operating System for Agent Memory
### A Complete Hackathon-Winning Blueprint

> **One-liner:** Engram replaces "stuff everything into context" with a living, structured **World Model** that agents read and write to — so a tiny model can run forever, get *smarter* over time, and cost the same on turn 10,000 as it did on turn 1.

---

## 1. The Best Enhanced Solution Idea

**The core insight:** Context windows are a *symptom*. The real disease is that agents treat memory as a *transcript* instead of a *model*. Humans don't remember every word of every conversation — we compress experience into **beliefs, entities, relationships, and episodes**, and we recall only what's relevant to the task at hand.

**Engram** is a memory substrate that sits between any LLM agent and the world. It maintains four continuously-updated memory layers instead of one giant growing prompt:

| Layer | What it holds | Analogy |
|---|---|---|
| **Working Memory** | The ~1-2K token "hot" bundle injected into the current prompt | RAM |
| **Semantic Memory** | Vector-indexed atomic facts ("Alice prefers dark mode") | Long-term facts |
| **Episodic Memory** | Compressed, timestamped summaries of past events, with decay | Diary |
| **Entity Graph** | A live knowledge graph of people/objects/tasks and their relationships | Mental model |

A background **Memory Compiler** (itself an LLM-powered pipeline) watches every new observation, extracts structured deltas (new entities, updated relationships, contradictions, resolved facts), merges them into the graph, and **consolidates** old episodes into higher-level summaries — exactly like memory consolidation during sleep.

When the agent needs to act, a **Context Compiler** doesn't dump history — it runs a hybrid retrieval (graph traversal + vector similarity + recency/importance scoring) and assembles a **just-in-time context bundle** capped at a fixed token budget, regardless of how long the agent has been running.

**Result:** Flat cost curve. Flat latency curve. Rising accuracy curve (because the world model gets *more* correct and *more* consolidated over time, not just longer).

---

## 2. Why This Solution Will Win the Hackathon

1. **It attacks the actual bottleneck**, not a symptom — judges immediately recognize this is a real, unsolved infra problem (this is literally what Letta/MemGPT, Mem0, and every agent-infra startup is racing to solve — you're playing in a space judges know is hot and valuable).
2. **It's demoable in real time.** You can *show* the graph growing, *show* the token count staying flat while a naive agent's grows linearly, and *show* a small/cheap model outperforming a raw-context agent on a long-horizon task.
3. **It's infrastructure, not a feature.** Judges reward things that could plug into *any* agent framework (LangChain, CrewAI, Claude Agent SDK, AutoGPT-style loops) — this reads as a platform/startup, not a toy app.
4. **Quantifiable, judge-friendly metrics**: tokens/turn, $/1000 turns, latency/turn, recall accuracy — numbers win arguments.
5. **Technically deep** (graph theory, vector retrieval, consolidation algorithms, decay functions) but the demo surface is dead simple: a chat + a live-updating brain visualization.

---

## 3. Unique Differentiators Competitors Won't Have

- **Memory Decay & Consolidation Engine** — most memory demos just append to a vector DB forever ("infinite memory" = still unbounded growth). Engram actively **forgets, merges, and compresses**, mimicking Ebbinghaus forgetting curves + importance-weighted retention. This is the difference between a bigger haystack and an actual model.
- **Contradiction Resolution** — when new info conflicts with old ("Alice moved to Berlin" vs "Alice lives in Delhi"), Engram doesn't just append — it timestamps, resolves, and marks the old fact as superseded, keeping the graph *consistent*.
- **Live "Brain Visualizer"** — a real-time animated knowledge graph (nodes pulse when accessed, fade when decaying, merge when consolidated). Nobody else demos memory *visually*.
- **Model-agnostic Context Budget Compiler** — you specify a token budget (e.g., "fit in 1,500 tokens for Haiku") and Engram guarantees the best possible bundle under that budget — this lets tiny/cheap models perform like large ones.
- **Explainability layer** — every fact in the context bundle is traceable ("why is this here?" → retrieval path: graph edge + recency score + relevance score). Judges love explainable AI.
- **Cost/Latency Flatline Dashboard** — a live chart proving the core claim numerically, not just narratively.

---

## 4. AI Features That Create WOW Factor

1. **Live Memory Compiler Agent** — visibly extracts structured facts from raw text in real time (stream the JSON diff on screen as it happens).
2. **"Ask the World Model"** — a debug console where judges can literally query the agent's brain directly ("What do you know about Alice?") and get a graph-traversal answer *without* calling the main LLM — proving the model is queryable, not just a blob.
3. **Auto-summarizing Sleep Cycle** — trigger a manual "consolidate memory" button; watch 50 episodic entries visually collapse into 3 summary nodes with an animated merge.
4. **Small-Model Superpowers Demo** — run the *same* long-horizon task (e.g., a 50-turn trip-planning conversation) on Claude Haiku with Engram vs. Haiku with raw context — Engram-Haiku stays coherent and cheap; raw-context-Haiku degrades/truncates/hallucinates.
5. **Memory Diff Replay** — a scrubber timeline that lets judges "rewind" the agent's brain to any point in the conversation and see exactly what it believed then.
6. **Conflict Detector Alerts** — a toast notification pops up live: "⚠️ Contradiction detected: resolving..." — visually proves the reasoning layer works.

---

## 5. Complete Modern Tech Stack

**Frontend**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS + shadcn/ui (polished components fast)
- **React Flow** or **Cytoscape.js** for the live knowledge-graph visualization
- Recharts for the cost/latency flatline dashboards
- Socket.io-client for real-time graph/event streaming
- Framer Motion for node pulse/fade/merge animations

**Backend**
- FastAPI (Python 3.11) — async, fast to build, great for AI pipelines
- Socket.io (python-socketio) for real-time push to frontend
- Pydantic for structured LLM output validation

**AI / Orchestration**
- **Claude (Anthropic API)** — agent reasoning + Memory Compiler extraction (use `claude-sonnet-4-6` for compiler quality, `claude-haiku-4-5` for the "small model superpowers" demo)
- Structured outputs via tool-use/JSON schema for fact extraction
- Sentence-Transformers (`all-MiniLM-L6-v2`, free, local, no API cost) or Voyage AI free tier for embeddings

**Data Layer**
- **PostgreSQL + pgvector** (Neon.tech free tier) — one database for both relational graph edges AND vector search = simpler than running Neo4j + separate vector DB under hackathon time pressure
- (Stretch) **Memgraph** or **Neo4j AuraDB Free** if you want a "real" graph DB for extra technical-depth points
- Redis (Upstash free tier) — working-memory hot cache, sub-millisecond context bundle assembly

**Infra / DevOps**
- GitHub Actions CI (lint + test on push) — shows production maturity
- Vercel (frontend) + Render/Railway (backend) — both free tiers, both deploy in minutes

---

## 6. Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Next.js)                            │
│  Chat UI │ Live Brain Graph (React Flow) │ Metrics Dashboard         │
└───────────────┬─────────────────────────────────┬────────────────────┘
                 │ REST/WebSocket                  │ WebSocket (live events)
┌────────────────▼─────────────────────────────────▼────────────────────┐
│                        FASTAPI BACKEND (Engram Core)                  │
│                                                                        │
│  ┌──────────────┐   ┌───────────────────┐   ┌───────────────────┐    │
│  │ Agent Runtime │──▶│ Context Compiler   │──▶│ Working Memory     │  │
│  │ (Claude API)  │   │ (budget-aware      │   │ Cache (Redis)      │  │
│  │               │   │  hybrid retrieval) │   │                    │  │
│  └──────┬────────┘   └─────────▲──────────┘   └────────────────────┘  │
│         │ raw observation      │ query                                │
│         ▼                      │                                      │
│  ┌──────────────┐       ┌──────┴────────┐      ┌────────────────┐    │
│  │ Memory        │──────▶│ World Model    │◀────▶│ Consolidation   │  │
│  │ Compiler       │extract│ Store          │      │ Engine (decay,  │  │
│  │ (LLM extractor)│facts │ - Entity Graph │      │ merge, sleep-   │  │
│  │               │      │ - Episodic log │      │ cycle summarize)│  │
│  └──────────────┘       │ - Semantic vecs │      └────────────────┘  │
│                          └───────┬─────────┘                          │
└──────────────────────────────────┼──────────────────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │ PostgreSQL + pgvector (Neon)   │
                    │ - entities, relations, edges   │
                    │ - episodic_memory (w/ decay)   │
                    │ - fact_embeddings (vector col) │
                    └───────────────────────────────┘
```

**Data flow in one loop:**
1. User/agent produces an observation → sent to **Memory Compiler**.
2. Compiler extracts structured deltas (entities, relations, facts, contradictions) via Claude tool-use → writes to **World Model Store**.
3. **Consolidation Engine** runs async: decays stale nodes, merges duplicate entities, compresses old episodes.
4. When the agent needs to respond, **Context Compiler** queries the store (graph traversal from relevant entities + vector similarity + recency/importance scoring), assembles a token-budgeted bundle, caches it in Redis as **Working Memory**.
5. Agent Runtime calls Claude with the compact bundle instead of full history.
6. Every step emits a WebSocket event → frontend animates the brain graph and updates metrics live.

---

## 7. Database Schema (PostgreSQL + pgvector)

```sql
-- Core entity table (people, objects, tasks, concepts)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,       -- person | object | task | concept | location
    importance_score FLOAT DEFAULT 0.5,
    last_accessed_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    decay_rate FLOAT DEFAULT 0.05,
    metadata JSONB
);

-- Relationships between entities (the graph edges)
CREATE TABLE relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    source_entity_id UUID REFERENCES entities(id),
    target_entity_id UUID REFERENCES entities(id),
    relation_type TEXT NOT NULL,     -- e.g. "prefers", "owns", "located_in"
    confidence FLOAT DEFAULT 1.0,
    valid_from TIMESTAMPTZ DEFAULT now(),
    superseded_by UUID REFERENCES relations(id),  -- contradiction resolution
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Atomic facts with vector embeddings (semantic memory)
CREATE TABLE facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    entity_id UUID REFERENCES entities(id),
    statement TEXT NOT NULL,
    embedding VECTOR(384),           -- pgvector, MiniLM dims
    importance_score FLOAT DEFAULT 0.5,
    superseded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Episodic memory (compressed event log, hierarchical)
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    summary TEXT NOT NULL,
    level INT DEFAULT 0,             -- 0 = raw turn, 1 = consolidated, 2 = meta-summary
    parent_episode_ids UUID[],       -- which raw episodes this summarizes
    embedding VECTOR(384),
    importance_score FLOAT DEFAULT 0.5,
    decayed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Working memory bundle snapshots (for the replay/scrubber feature)
CREATE TABLE context_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    turn_number INT NOT NULL,
    token_count INT NOT NULL,
    bundle_json JSONB NOT NULL,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for speed
CREATE INDEX ON facts USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON episodes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON entities (session_id, importance_score DESC);
```

---

## 8. API Structure

```
POST   /sessions                        → create a new agent session
POST   /sessions/{id}/observe            → ingest a raw observation (triggers Memory Compiler)
GET    /sessions/{id}/graph              → full entity/relation graph for visualization
GET    /sessions/{id}/context-bundle     → get current working-memory bundle (+ token count)
POST   /sessions/{id}/query              → "Ask the World Model" direct graph/vector query
POST   /sessions/{id}/agent-turn         → run one agent reasoning step (uses compiled context)
POST   /sessions/{id}/consolidate        → manually trigger the "sleep cycle"
GET    /sessions/{id}/metrics            → token/cost/latency time series
GET    /sessions/{id}/bundles/{turn}     → historical bundle for the replay scrubber
WS     /sessions/{id}/live               → real-time event stream (graph updates, compiler logs)
```

All extraction endpoints return **strict JSON** (Claude tool-use / structured output) validated against Pydantic models — no regex parsing, no flaky string matching.

---

## 9. Frontend + Backend Plan

**Backend build order:**
1. Session + observation ingestion endpoints
2. Memory Compiler (Claude tool-use extraction → entities/relations/facts)
3. World Model Store (Postgres writes, dedup/merge logic)
4. Context Compiler (hybrid retrieval + token-budget packing)
5. Agent Runtime loop (calls Claude with compiled bundle)
6. Consolidation Engine (decay + summarization job)
7. WebSocket event emitter wired into every step above
8. Metrics aggregation endpoint

**Frontend build order:**
1. Chat interface (send observation → see agent reply)
2. Live Brain Graph (React Flow, subscribes to WebSocket)
3. Metrics dashboard (flat-line token/cost chart vs. simulated baseline)
4. "Ask the World Model" debug console
5. Replay scrubber (pull historical `context_bundles`)
6. Polish pass: animations, dark theme, onboarding tour

---

## 10. Stunning UI/UX Strategy

- **Split-screen demo layout**: left = chat, right = living brain graph. Judges watch the brain *grow* while you talk to the agent — this alone is the single biggest "wow" per second of demo time.
- **Dark, "neural" aesthetic**: deep navy/charcoal background, glowing cyan/violet nodes, particle-style edges — looks like a sci-fi command center, not a CRUD app.
- **Node behavior tells the story without words**: new node = spawn animation; accessed node = pulse/glow; decaying node = fade to gray; merged nodes = magnetic-merge animation into a consolidated node.
- **Always-visible token counter** pinned in the corner, ticking in real time, visibly *not* climbing — the single strongest visual proof of your core claim.
- **One-click "Naive Agent" comparison toggle** — same conversation, side-by-side token/cost graph where the baseline line rockets up and MnemOS stays flat.
- **Micro-copy that explains itself**: small labels like "🧠 consolidating 12 episodes → 1 summary" so non-technical judges instantly get it.

---

## 11. MVP Features for Quick Building (build these first)

1. Session creation + chat loop with Claude
2. Memory Compiler: extract entities/facts from each turn (structured output)
3. Postgres storage of entities/facts (skip relations graph complexity if time-tight)
4. Simple Context Compiler: top-K vector-similarity facts + last N episodes, packed to a token budget
5. Live token-count display (before/after comparison, even if static baseline is simulated)
6. Basic React Flow graph rendering entities as nodes (no fancy animation yet)
7. One end-to-end working demo scenario (e.g., a travel-planning assistant over 20+ turns)

---

## 12. Advanced Features for Judge Impact (add if time remains)

1. Full relation-graph with contradiction resolution + "superseded_by" visualization
2. Consolidation/"sleep cycle" with animated node merging
3. Replay scrubber across the whole session
4. "Ask the World Model" query console bypassing the main LLM
5. Real naive-agent baseline running in parallel (not simulated) for an honest side-by-side
6. Multi-agent support: two agents sharing one World Model (proves it's infra, not a single-chatbot trick)
7. Exportable World Model as portable JSON — "memory you can move between models"
8. Decay-rate tuning UI (importance sliders) — shows configurability for real product use

---

## 13. Free APIs / Tools / Services to Use

| Purpose | Free Tool |
|---|---|
| LLM reasoning + extraction | Anthropic Claude API (Console free credits) |
| Embeddings | `sentence-transformers` (local, $0) or Voyage AI free tier |
| Database | Neon.tech (Postgres + pgvector, free tier) |
| Cache | Upstash Redis (free tier) |
| Graph DB (stretch) | Neo4j AuraDB Free / Memgraph Cloud free tier |
| Frontend hosting | Vercel (free) |
| Backend hosting | Render or Railway (free tier) |
| Real-time | Socket.io (open source, self-hosted) |
| Graph visualization | React Flow / Cytoscape.js (open source) |
| Charts | Recharts (open source) |
| CI | GitHub Actions (free for public repos) |

---

## 14. Deployment Strategy

- **Frontend** → Vercel, auto-deploy from `main` branch, environment variables for API base URL.
- **Backend** → Render/Railway deploy; expose REST + WebSocket on same service.
- **Database** → Neon Postgres (serverless, free tier, pgvector extension enabled via `CREATE EXTENSION vector;`).
- **Redis** → Upstash, connect via REST or TCP.
- **Secrets** → `.env` locally, provider dashboard env vars in prod; never commit keys.

- **Fallback for demo day**: pre-seed a session with an interesting conversation history in case live API calls are rate-limited — always have a recorded backup video.

---

## 15. 24-Hour Hackathon Execution Roadmap

**Hours 0–2: Foundation**
- Repo scaffold, Postgres schema migration, FastAPI skeleton, Next.js skeleton, deploy pipelines connected end-to-end with a "hello world" round trip.

**Hours 2–6: Core Memory Loop**
- Build Memory Compiler (Claude structured extraction), entities/facts tables wired, basic Context Compiler (vector top-K + budget cap), Agent Runtime using compiled bundle.

**Hours 6–10: Make It Visible**
- WebSocket event stream, React Flow graph rendering live entity nodes, token counter widget, basic chat UI polish.

**Hours 10–14: The Wow Layer**
- Relation graph + contradiction resolution, consolidation/sleep-cycle job with merge animation, "Ask the World Model" console.

**Hours 14–18: Comparison & Metrics**
- Naive-agent baseline path, side-by-side metrics dashboard (token/cost/latency flatline chart), replay scrubber.

**Hours 18–21: Polish & Harden**
- UI animation pass, dark theme, error handling, seed a compelling demo scenario, write copy/labels, cross-browser check.

**Hours 21–23: Deploy & Rehearse**
- Final deploy, smoke test on deployed URLs (not just localhost), record backup demo video, rehearse pitch twice with a timer.

**Hour 23–24: Submission**
- README, PPT, pitch script finalized, submit early — never at the buzzer.

---

## 16. Judge-Focused Demo Strategy

1. **Open with the pain, visually**: show a naive agent's context bar filling up and slowing down/costing more as it "remembers" — 15 seconds, no words needed.
2. **Cut to Engram**: same scenario, brain graph blooming on screen, token counter staying flat. Let the contrast do the persuading.
3. **Live interaction**: type a new message that contradicts an earlier fact ("Actually, I'm vegetarian now") — show the contradiction-resolution toast fire in real time.
4. **Hit "consolidate memory"** — watch nodes visually merge — narrate it as "this is literally how the agent sleeps and compresses its day."
5. **Close on the metrics dashboard**: flat line vs. rising line, with a dollar-cost projection ("at 10,000 turns, naive costs $X, Engram costs $Y").
6. **End with the platform pitch**: "This isn't a chatbot — it's a memory layer any agent framework can plug into."

---

## 17. 2-Minute Winning Pitch

> "Every AI agent today has the same disease: it remembers by *hoarding*. Stuff every message into the context window, and the agent gets slower, dumber, and more expensive the longer it runs. That's not memory — that's a transcript.
>
> We built **Engram** — an operating system for agent memory. Instead of a growing pile of text, Engram keeps a living, structured model of the world: entities, relationships, facts, and compressed episodes — constantly updated, constantly consolidated, and just-in-time compiled into a tiny context bundle for whatever the agent needs *right now*.
>
> [Show the brain graph blooming and the token counter staying flat.]
>
> Watch this: our agent just ran 50 turns of a real conversation. A naive agent's context grew to 12,000 tokens and $0.09 a turn. Engram stayed at 1,400 tokens and 2 cents — on a *cheaper* model — and it never lost a fact, because when I said I moved to Berlin, it didn't just remember that — it *updated* what it believed and forgot what was no longer true.
>
> This is infrastructure any agent framework can plug into — LangChain, CrewAI, custom agent loops — because the problem isn't which LLM you use. It's how it remembers. Engram is the memory layer the next generation of AI agents will run on."

---

## 18. Likely Judge Questions with Winning Answers

**Q: How is this different from RAG / a vector database memory?**
A: RAG retrieves *chunks of text*. Engram maintains a *structured, self-correcting model* — it resolves contradictions, decays stale facts, and consolidates episodes hierarchically. A vector DB never forgets or merges; it just grows. Ours actively curates.

**Q: How is this different from MemGPT/Letta or Mem0?**
A: Great question — we're inspired by that space. Our differentiators are the **explicit contradiction-resolution graph**, **visual explainability** (you can see *why* a fact was retrieved), and a **hard token-budget compiler** that guarantees a fixed context size regardless of session length, making it trivially portable to small/cheap models.

**Q: Does this scale to millions of users/sessions?**
A: Yes — each session's World Model is isolated by `session_id`, Postgres + pgvector scales horizontally, and the consolidation job is a background async task, so it doesn't block the hot path. Long term we'd shard by session and use a managed graph DB.

**Q: What happens if the extraction LLM makes a mistake?**
A: Every fact carries a confidence score and provenance (which turn it came from). Low-confidence facts are weighted down in retrieval, and contradictions surface visibly instead of silently corrupting memory — this is strictly safer than raw context, where a hallucinated fact just sits invisibly in a huge prompt.

**Q: Is this only useful for chatbots?**
A: No — this is for *any* long-running agent: coding agents, customer-support agents, autonomous research agents, robotics agents. Anywhere an agent runs longer than one context window fits.

**Q: What's the business model?**
A: Memory-as-a-service API/SDK — usage-based pricing per compiled context bundle, similar to how vector DB startups (Pinecone) or memory startups (Mem0) monetize, but positioned on cost savings we can prove.

---

## 19. Professional PPT Structure (10 slides)

1. **Title** — Engram + tagline + team
2. **The Problem** — context windows don't scale; cost/latency graph rising
3. **The Insight** — memory ≠ transcript; memory = model
4. **The Solution** — 4-layer architecture diagram
5. **Live Demo** (screenshot/GIF of brain graph + token counter)
6. **Architecture Deep Dive** — system diagram from Section 6
7. **What Makes This Different** — differentiator table
8. **Metrics That Matter** — flatline chart, cost projection at scale
9. **Roadmap / Business Potential** — SDK, plug into LangChain/CrewAI, pricing model
10. **Team + Ask** — what you're looking for (mentorship, prize, next steps)

---

## 20. Technical Documentation Content

- **Overview & Problem Statement**
- **Architecture** (with the diagram from Section 6)
- **Memory Model Spec**: entity schema, relation schema, decay function math, consolidation trigger conditions
- **Context Compiler Algorithm**: retrieval scoring formula (e.g., `score = w1*similarity + w2*recency + w3*importance - w4*decay`), token-budget packing (knapsack-style greedy selection)
- **API Reference** (Section 8, with request/response examples)
- **Setup & Local Development Guide**
- **Evaluation Methodology**: how token/cost/latency benchmarks were measured, naive-agent baseline definition
- **Known Limitations & Future Work**

---

## 21. README.md Structure

```markdown
# Engram 🧠 — The Operating System for Agent Memory

> Structured world models for AI agents. Flat cost. Flat latency. Rising accuracy.

## The Problem
## The Solution (with architecture GIF)
## Demo (link + screenshots)
## Quick Start
   - Local setup instructions
   - Environment variables needed
## Architecture Overview (diagram)
## Tech Stack
## API Reference (link to docs)
## Benchmarks (flatline chart image)
## Roadmap
## Team
## License
```

---

## 22. Resume-Ready Project Description

> **Engram — Structured Memory Infrastructure for AI Agents** *(Hackathon Project)*
> Designed and built a memory architecture that replaces linear context-window growth with a structured, continuously-consolidated world model (entity graph + episodic + semantic memory), achieving flat token cost and latency across 50+ turn agent sessions vs. linear growth in a naive baseline. Built a hybrid retrieval engine (graph traversal + vector similarity + recency/importance scoring) with a hard token-budget compiler, a real-time knowledge-graph visualization (React Flow + WebSockets), and a contradiction-resolution system for self-correcting memory. Stack: Next.js, FastAPI, PostgreSQL/pgvector, Redis, Claude API, Socket.io.

---

## 23. GitHub-Ready Folder Structure

```
engram/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # chat + brain graph split view
│   │   ├── dashboard/page.tsx       # metrics dashboard
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── BrainGraph.tsx           # React Flow graph
│   │   ├── TokenCounter.tsx
│   │   ├── MetricsChart.tsx
│   │   └── ReplayScrubber.tsx
│   ├── lib/socket.ts
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── routers/
│   │   │   ├── sessions.py
│   │   │   ├── observe.py
│   │   │   ├── query.py
│   │   │   └── metrics.py
│   │   ├── core/
│   │   │   ├── memory_compiler.py   # Claude extraction pipeline
│   │   │   ├── context_compiler.py  # hybrid retrieval + budget packing
│   │   │   ├── consolidation.py     # decay + merge engine
│   │   │   └── agent_runtime.py
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   └── ws/events.py
│   ├── tests/
│   └── requirements.txt
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── BENCHMARKS.md
├── .gitignore
├── .github/workflows/ci.yml
├── README.md
└── LICENSE
```

---

## A COMPLETE WINNING EXECUTION BLUEPRINT

**Idea →** Stop treating agent memory as a growing transcript; build Engram, a structured, self-correcting world model (entity graph + episodic + semantic + working memory) that's queried, not replayed.

**Architecture →** FastAPI core with a Memory Compiler (LLM extraction), a World Model Store (Postgres + pgvector), a Consolidation Engine (decay/merge), and a Context Compiler (hybrid retrieval, token-budgeted) feeding a Claude-powered Agent Runtime — all streamed live via WebSockets.

**Coding →** Build in the 24-hour order from Section 15: foundation → core memory loop → visibility layer → wow features → comparison metrics → polish → deploy.

**Deployment →** Vercel (frontend) + Render/Railway (backend) + Neon Postgres + Upstash Redis, all free-tier.

**Presentation →** Split-screen live demo (chat + blooming brain graph + flatline token counter) is your entire argument — let judges *see* the claim, then close with the 2-minute pitch from Section 17.

**Judging Strategy →** Win on the trifecta judges actually score: **technical depth** (graph + vector + decay + consolidation algorithms), **visual wow** (live animated brain, flatline chart), and **real-world credibility** (positioned as pluggable infra/SDK, not a one-off chatbot) — while having crisp, rehearsed answers ready for the RAG/MemGPT comparison question, because that's the one every judge will ask.

**The single sentence that wins the room:** *"We didn't make the agent remember more — we made it remember better."*
