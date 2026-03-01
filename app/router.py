import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    AgentCreate, AgentResponse,
    RememberRequest, MemoryResponse,
    RecallRequest, RecallResponse,
    InjectContextRequest, InjectContextResponse,
)
import app.service as svc

router = APIRouter()


# ── Agents ─────────────────────────────────────────────────────────────────────

@router.post("/agents", response_model=AgentResponse, status_code=201,
             summary="Create a new agent memory space")
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await svc.create_agent(db, data)


@router.get("/agents", response_model=list[AgentResponse],
            summary="List all agents")
async def list_agents(db: AsyncSession = Depends(get_db)):
    return await svc.list_agents(db)


@router.get("/agents/{agent_id}", response_model=AgentResponse,
            summary="Get a single agent")
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description,
        metadata=agent.metadata_, created_at=agent.created_at,
    )


# ── Memory: Remember ───────────────────────────────────────────────────────────

@router.post("/agents/{agent_id}/remember", response_model=MemoryResponse, status_code=201,
             summary="Store a new memory")
async def remember(
    agent_id: uuid.UUID,
    data: RememberRequest,
    db: AsyncSession = Depends(get_db),
):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await svc.remember(db, agent_id, data)


# ── Memory: Recall ─────────────────────────────────────────────────────────────

@router.post("/agents/{agent_id}/recall", response_model=RecallResponse,
             summary="Retrieve relevant memories by semantic similarity")
async def recall(
    agent_id: uuid.UUID,
    data: RecallRequest,
    db: AsyncSession = Depends(get_db),
):
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await svc.recall(db, agent_id, data)


# ── Memory: Inject Context (killer feature) ────────────────────────────────────

@router.post("/agents/{agent_id}/inject-context", response_model=InjectContextResponse,
             summary="Get a ready-to-inject context block for your LLM prompt")
async def inject_context(
    agent_id: uuid.UUID,
    data: InjectContextRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    The killer endpoint.

    Pass the user's current message → get back a formatted context string
    you can prepend directly to your system prompt.

    Your agent goes from amnesiac to contextually aware in 1 API call.
    """
    agent = await svc.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await svc.inject_context(db, agent_id, data)


# ── Memory: Delete ─────────────────────────────────────────────────────────────

@router.delete("/agents/{agent_id}/memories/{memory_id}", status_code=204,
               summary="Delete a specific memory")
async def delete_memory(
    agent_id: uuid.UUID,
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await svc.delete_memory(db, agent_id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")


@router.delete("/agents/{agent_id}/memories", status_code=200,
               summary="Wipe all memories for an agent")
async def delete_all_memories(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    count = await svc.delete_all_memories(db, agent_id)
    return {"deleted": count}
