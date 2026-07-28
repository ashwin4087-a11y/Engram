# Engram — Memory OS

Engram is a structured memory system (a "World Model") for AI agents. It gives agents persistent, structured memory across conversations, allowing them to maintain long-term context without blowing up the context window.

## Key Features

- **Knowledge Graph**: Extracts entities, facts, and relationships dynamically as you chat.
- **Constant-Size Context**: Recompiles a token-budget-aware context bundle for every turn. Context window usage flatlines while knowledge grows indefinitely.
- **Sleep Cycles (Consolidation)**: Periodically merges related memories, resolves contradictions, and prunes stale facts.
- **Contradiction Detection**: Alerts in real-time when the agent detects conflicting information.
- **Time Travel Replay**: Scrub through the history to see exactly what context the agent was given at any specific turn.

## Architecture

- **Backend**: Python / FastAPI / SQLAlchemy / Postgres (pgvector) / Redis / Socket.IO
- **Frontend**: Next.js / React / TailwindCSS / ReactFlow

## Running Locally

Engram uses `ollama` by default for the local, free LLM provider.

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL (with pgvector extension)
- Redis
- Ollama (running locally)

### 1. Setup Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate

pip install -r requirements.txt

# Environment config
cp .env.example .env
```

Ensure your PostgreSQL and Redis instances are running and configured in `.env`.

Run the backend dev server:
```bash
uvicorn main:application --host 0.0.0.0 --port 8000 --reload
```

### 2. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (or 3001 if 3000 is in use) to view the application.

## Troubleshooting

- **Socket.IO not connecting:** Ensure the backend is running on `http://localhost:8000`.
- **Database errors:** Ensure Postgres is running and `pgvector` is installed.
