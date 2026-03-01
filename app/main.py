from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB tables + pgvector extension
    await init_db()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Agent Memory Layer",
    description="""
## Give your AI agents long-term memory. 🧠

The **Agent Memory Layer** is a plug-and-play API that solves the #1 problem
in production AI agents: they forget everything between sessions.

### Core endpoints

| Endpoint | What it does |
|---|---|
| `POST /agents/{id}/remember` | Store a memory (text → embedding → pgvector) |
| `POST /agents/{id}/recall` | Find relevant memories by semantic similarity |
| `POST /agents/{id}/inject-context` | **Get a ready-to-inject context block for your LLM** |

### Quick start

```python
import httpx

BASE = "http://localhost:8000"

# 1. Create an agent
agent = httpx.post(f"{BASE}/agents", json={"name": "support-bot"}).json()
agent_id = agent["id"]

# 2. Store memories
httpx.post(f"{BASE}/agents/{agent_id}/remember", json={
    "content": "User Alice has a platinum subscription and prefers email contact",
    "memory_type": "semantic",
    "metadata": {"entity": "Alice", "importance": "high"}
})

# 3. Inject context before your LLM call
ctx = httpx.post(f"{BASE}/agents/{agent_id}/inject-context", json={
    "message": "I have a billing issue"
}).json()

system_prompt = ctx["context_block"] + "\\n\\nYou are a helpful support agent."
# → Your LLM now knows about Alice before you even ask
```
    """,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-memory-layer"}
