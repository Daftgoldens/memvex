import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ApiKey, Agent
from app.schemas import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse, ApiKeyDemoCreate, DemoKeyCreatedResponse
from app.auth import create_api_key, create_demo_key, get_api_key

router = APIRouter(tags=["Authentication"])


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=201,
             summary="Create an API key (admin)")
async def create_key(data: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    api_key, full_key = await create_api_key(db, data.name)
    return ApiKeyCreatedResponse(
        id=api_key.id, name=api_key.name, key_prefix=api_key.key_prefix,
        is_active=api_key.is_active, is_demo=api_key.is_demo,
        memory_limit=api_key.memory_limit, created_at=api_key.created_at,
        last_used_at=api_key.last_used_at, full_key=full_key,
    )


@router.post("/demo", response_model=DemoKeyCreatedResponse, status_code=201,
             summary="Get a free demo API key",
             description="Creates a demo key limited to 100 memories. One key per email.")
async def create_demo(data: ApiKeyDemoCreate, db: AsyncSession = Depends(get_db)):
    # Bloquer si l'email a déjà une clé demo active
    existing = await db.execute(
        select(ApiKey).where(
            ApiKey.contact_email == data.email,
            ApiKey.is_demo == True,
            ApiKey.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="A demo key already exists for this email. Check your inbox or contact us to upgrade."
        )

    # Créer la clé
    api_key, full_key = await create_demo_key(db, data.name, data.email, data.usecase)

    # Créer automatiquement un premier agent
    agent = Agent(
        name=f"{data.name}'s agent",
        description="Auto-created demo agent",
        api_key_id=api_key.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return DemoKeyCreatedResponse(
        full_key=full_key,
        agent_id=str(agent.id),
        memory_limit=100,
        message="Ready! Your API key and first agent are set up.",
    )


@router.get("/keys", response_model=list[ApiKeyResponse], summary="List your API keys")
async def list_keys(api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key.id))
    return result.scalars().all()


@router.delete("/keys/{key_id}", status_code=204, summary="Revoke an API key")
async def revoke_key(key_id: uuid.UUID, api_key: ApiKey = Depends(get_api_key), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.id == api_key.id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    key.is_active = False
    await db.commit()
