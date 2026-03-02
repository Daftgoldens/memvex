# 🧠 Memvex

**Give your AI agents long-term memory. One API. Three endpoints.**

The #1 problem in production AI agents: they forget everything between sessions.
This is the infrastructure layer that fixes that.

## Architecture

```
Your Agent  →  POST /remember  →  text → embedding → pgvector
Your Agent  →  POST /recall    →  query → cosine similarity → top-K memories
Your Agent  →  POST /inject-context  →  message → formatted context block ✨
```

## Quick start

```bash
# 1. Clone & setup
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start the stack
docker compose up

# 3. API is live at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Core endpoints

### Store a memory
```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/remember \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Alice prefers email contact and has a platinum subscription",
    "memory_type": "semantic",
    "metadata": {"entity": "Alice"}
  }'
```

### Recall relevant memories
```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How should I contact Alice?",
    "top_k": 5,
    "threshold": 0.75
  }'
```

### Inject context (the killer feature)
```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/inject-context \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a billing issue"}'
```

Returns a ready-to-use context block to prepend to your system prompt:
```
[AGENT MEMORY CONTEXT]
- Alice has a platinum subscription (similarity: 0.92)
- Last session: Alice was frustrated about response times (similarity: 0.87)
```

## Memory types

| Type | Use case |
|---|---|
| `episodic` | Events, past interactions, conversations |
| `semantic` | Facts about users, entities, preferences |
| `procedural` | How-to knowledge, processes, procedures |

## Stack

- **FastAPI** — async Python API
- **PostgreSQL + pgvector** — vector storage with HNSW index
- **OpenAI** — `text-embedding-3-small` embeddings (1536 dims)
- **SQLAlchemy** — async ORM

## Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Roadmap

- [ ] SDK Python (`pip install agent-memory`)
- [ ] SDK TypeScript (`npm install agent-memory`)
- [ ] LangChain / LlamaIndex integration
- [ ] Memory decay & importance scoring
- [ ] Multi-tenant auth (API keys per agent)
- [ ] Streaming recall
- [ ] Dashboard UI
