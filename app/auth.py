import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ApiKey, Memory, Agent

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
KEY_PREFIX = "sk-mem-"
DEMO_MEMORY_LIMIT = 100


def _generate_key() -> tuple[str, str, str]:
    raw = secrets.token_urlsafe(32)
    full_key = f"{KEY_PREFIX}{raw}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:18] + "..."
    return full_key, key_hash, key_prefix


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(db: AsyncSession, name: str) -> tuple[ApiKey, str]:
    """Clé normale — sans limite."""
    full_key, key_hash, key_prefix = _generate_key()
    api_key = ApiKey(key_hash=key_hash, key_prefix=key_prefix, name=name, is_demo=False, memory_limit=None)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, full_key


async def create_demo_key(db: AsyncSession, name: str, email: str, usecase: str) -> tuple[ApiKey, str]:
    """Clé de démo — limitée à 100 mémoires, créée depuis la landing page."""
    full_key, key_hash, key_prefix = _generate_key()
    api_key = ApiKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=f"[DEMO] {name}",
        is_demo=True,
        memory_limit=DEMO_MEMORY_LIMIT,
        contact_email=email,
        contact_usecase=usecase,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, full_key


async def get_api_key(
    header_key: str | None = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    if not header_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing API key. Add header: X-API-Key: sk-mem-...")
    key_hash = _hash_key(header_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API key.")
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return api_key


async def check_memory_limit(db: AsyncSession, api_key: ApiKey) -> None:
    """Lève une 402 si la clé de démo a atteint sa limite de mémoires."""
    if api_key.memory_limit is None:
        return  # illimité
    # Compter toutes les mémoires sous cette clé
    result = await db.execute(
        select(func.count(Memory.id))
        .join(Agent, Agent.id == Memory.agent_id)
        .where(Agent.api_key_id == api_key.id)
    )
    count = result.scalar_one()
    if count >= api_key.memory_limit:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "memory_limit_reached",
                "message": f"Demo limit of {api_key.memory_limit} memories reached. Contact us to upgrade.",
                "memories_used": count,
                "limit": api_key.memory_limit,
                "upgrade_url": "https://daftgoldens.github.io/memvex/#pricing",
            }
        )
