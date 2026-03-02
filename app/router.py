import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ApiKey
from app.auth import get_api_key
from app.schemas import (
    AgentCreate, AgentResponse,
    RememberRequest, MemoryResponse,
    RecallRequest, RecallResponse,
    InjectContextRequest, InjectContextResponse,
)
import app.service as svc

router = APIRouter(dependencies=[Depends(get_api_key)])


async def _get_agent_or_404(agent_id: uuid.UUID, api_key: ApiKey, db: AsyncSession):
    agent = await svc.get_agent(db, agent_id, api_key_id=api_key.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate, api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    return await svc.create_agent(db, data, api_key_id=api_key.id)


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    return await svc.list_agents(db, api_key_id=api_key.id)


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: uuid.UUID, api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_or_404(agent_id, api_key, db)
    return AgentResponse(id=agent.id, name=agent.name, description=agent.description,
                         metadata=agent.metadata_, created_at=agent.created_at)


@router.post("/agents/{agent_id}/remember", response_model=MemoryResponse, status_code=201)
async def remember(agent_id: uuid.UUID, data: RememberRequest,
                   api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, api_key, db)
    return await svc.remember(db, agent_id, data, api_key)  # on passe api_key pour la limite


@router.post("/agents/{agent_id}/recall", response_model=RecallResponse)
async def recall(agent_id: uuid.UUID, data: RecallRequest,
                 api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, api_key, db)
    return await svc.recall(db, agent_id, data)


@router.post("/agents/{agent_id}/inject-context", response_model=InjectContextResponse)
async def inject_context(agent_id: uuid.UUID, data: InjectContextRequest,
                         api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, api_key, db)
    return await svc.inject_context(db, agent_id, data)


@router.delete("/agents/{agent_id}/memories/{memory_id}", status_code=204)
async def delete_memory(agent_id: uuid.UUID, memory_id: uuid.UUID,
                        api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, api_key, db)
    if not await svc.delete_memory(db, agent_id, memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")


@router.delete("/agents/{agent_id}/memories", status_code=200)
async def delete_all_memories(agent_id: uuid.UUID,
                               api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, api_key, db)
    count = await svc.delete_all_memories(db, agent_id)
    return {"deleted": count}
