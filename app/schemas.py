import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ── Agent ──────────────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    metadata: dict = {}

class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    metadata: dict = {}
    created_at: datetime
    memory_count: int = 0
    model_config = {"from_attributes": True}


# ── Memory ─────────────────────────────────────────────────────────────────────

class RememberRequest(BaseModel):
    content: str = Field(..., min_length=1)
    session_id: str | None = None
    memory_type: str = "episodic"
    metadata: dict = {}

class MemoryResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    content: str
    session_id: str | None = None
    memory_type: str
    metadata: dict = {}
    created_at: datetime
    access_count: int = 0
    model_config = {"from_attributes": True}

class RecallRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    session_id: str | None = None
    memory_type: str | None = None

class RecallResult(BaseModel):
    memory: MemoryResponse
    similarity: float

class RecallResponse(BaseModel):
    query: str
    results: list[RecallResult]
    total_found: int

class InjectContextRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.75, ge=0.0, le=1.0)

class InjectContextResponse(BaseModel):
    context_block: str
    memories_used: int
    memories: list[RecallResult]


# ── Auth ───────────────────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class ApiKeyDemoCreate(BaseModel):
    """Créée depuis la landing page — clé de démo avec limite 100 mémoires."""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=255)
    usecase: str = Field(..., min_length=10, max_length=1000, description="Describe your agent use case")

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    is_demo: bool
    memory_limit: int | None
    created_at: datetime
    last_used_at: datetime | None = None
    model_config = {"from_attributes": True}

class ApiKeyCreatedResponse(ApiKeyResponse):
    full_key: str = Field(..., description="Store this securely — shown only once!")

class DemoKeyCreatedResponse(BaseModel):
    """Réponse simplifiée pour la landing page."""
    full_key: str
    memory_limit: int
    message: str
