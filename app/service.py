import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Memory
from app.schemas import (
    AgentCreate, AgentResponse,
    RememberRequest, MemoryResponse,
    RecallRequest, RecallResult, RecallResponse,
    InjectContextRequest, InjectContextResponse,
)
from app.embeddings import embed
from app.config import settings


# ── Agent CRUD ─────────────────────────────────────────────────────────────────

async def create_agent(db: AsyncSession, data: AgentCreate) -> AgentResponse:
    agent = Agent(name=data.name, description=data.description, metadata_=data.metadata)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        metadata=agent.metadata_,
        created_at=agent.created_at,
        memory_count=0,
    )


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def list_agents(db: AsyncSession) -> list[AgentResponse]:
    # Get agents with their memory counts
    result = await db.execute(
        select(Agent, func.count(Memory.id).label("memory_count"))
        .outerjoin(Memory, Memory.agent_id == Agent.id)
        .group_by(Agent.id)
        .order_by(Agent.created_at.desc())
    )
    rows = result.all()
    return [
        AgentResponse(
            id=a.id, name=a.name, description=a.description,
            metadata=a.metadata_, created_at=a.created_at,
            memory_count=count,
        )
        for a, count in rows
    ]


# ── Memory operations ──────────────────────────────────────────────────────────

async def remember(
    db: AsyncSession,
    agent_id: uuid.UUID,
    data: RememberRequest,
) -> MemoryResponse:
    """Store a new memory with its embedding."""

    # Generate embedding
    vector = await embed(data.content)

    memory = Memory(
        agent_id=agent_id,
        content=data.content,
        embedding=vector,
        session_id=data.session_id,
        memory_type=data.memory_type,
        metadata_=data.metadata,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    return _memory_to_schema(memory)


async def recall(
    db: AsyncSession,
    agent_id: uuid.UUID,
    data: RecallRequest,
) -> RecallResponse:
    """Find the most relevant memories using cosine similarity."""

    # Embed the query
    query_vector = await embed(data.query)

    # Build the similarity query using pgvector's <=> operator (cosine distance)
    # cosine_similarity = 1 - cosine_distance
    similarity_expr = (1 - Memory.embedding.cosine_distance(query_vector)).label("similarity")

    stmt = (
        select(Memory, similarity_expr)
        .where(
            Memory.agent_id == agent_id,
            # Filter by minimum similarity (threshold)
            (1 - Memory.embedding.cosine_distance(query_vector)) >= data.threshold,
        )
        .order_by(similarity_expr.desc())
        .limit(data.top_k)
    )

    # Optional filters
    if data.session_id:
        stmt = stmt.where(Memory.session_id == data.session_id)
    if data.memory_type:
        stmt = stmt.where(Memory.memory_type == data.memory_type)

    result = await db.execute(stmt)
    rows = result.all()

    # Update access tracking
    now = datetime.now(timezone.utc)
    for memory, _ in rows:
        memory.last_accessed_at = now
        memory.access_count += 1
    await db.commit()

    results = [
        RecallResult(memory=_memory_to_schema(m), similarity=round(float(sim), 4))
        for m, sim in rows
    ]

    return RecallResponse(
        query=data.query,
        results=results,
        total_found=len(results),
    )


async def inject_context(
    db: AsyncSession,
    agent_id: uuid.UUID,
    data: InjectContextRequest,
) -> InjectContextResponse:
    """
    High-level endpoint: given a user message, return a formatted context block
    ready to inject into your LLM system prompt.

    Example output injected before your system prompt:
    ─────────────────────────────────────────
    [AGENT MEMORY CONTEXT]
    - The user prefers concise answers (similarity: 0.92)
    - Last session: user was debugging a FastAPI auth issue (similarity: 0.88)
    - User's stack: Python, FastAPI, PostgreSQL (similarity: 0.85)
    ─────────────────────────────────────────
    """
    recall_result = await recall(
        db, agent_id,
        RecallRequest(
            query=data.message,
            top_k=data.top_k,
            threshold=data.threshold,
        )
    )

    if not recall_result.results:
        return InjectContextResponse(
            context_block="",
            memories_used=0,
            memories=[],
        )

    lines = ["[AGENT MEMORY CONTEXT]"]
    for r in recall_result.results:
        lines.append(f"- {r.memory.content} (similarity: {r.similarity})")

    context_block = "\n".join(lines)

    return InjectContextResponse(
        context_block=context_block,
        memories_used=len(recall_result.results),
        memories=recall_result.results,
    )


async def delete_memory(db: AsyncSession, agent_id: uuid.UUID, memory_id: uuid.UUID) -> bool:
    result = await db.execute(
        delete(Memory)
        .where(Memory.id == memory_id, Memory.agent_id == agent_id)
        .returning(Memory.id)
    )
    await db.commit()
    return result.scalar_one_or_none() is not None


async def delete_all_memories(db: AsyncSession, agent_id: uuid.UUID) -> int:
    result = await db.execute(
        delete(Memory).where(Memory.agent_id == agent_id).returning(Memory.id)
    )
    await db.commit()
    return len(result.fetchall())


# ── Helper ─────────────────────────────────────────────────────────────────────

def _memory_to_schema(m: Memory) -> MemoryResponse:
    return MemoryResponse(
        id=m.id,
        agent_id=m.agent_id,
        content=m.content,
        session_id=m.session_id,
        memory_type=m.memory_type,
        metadata=m.metadata_,
        created_at=m.created_at,
        access_count=m.access_count,
    )
