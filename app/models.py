import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.config import settings


class Agent(Base):
    """Represents an AI agent with its own isolated memory space."""
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    memories: Mapped[list["Memory"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class Memory(Base):
    """A single memory unit — text + its vector embedding + metadata."""
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )

    # The original text content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Vector embedding (1536 dims for text-embedding-3-small)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.embedding_dimensions), nullable=False
    )

    # Optional session context — group memories by conversation
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Memory type: episodic | semantic | procedural
    memory_type: Mapped[str] = mapped_column(String(50), default="episodic")

    # Arbitrary metadata (entities extracted, importance score, source, etc.)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_count: Mapped[int] = mapped_column(default=0)

    agent: Mapped["Agent"] = relationship(back_populates="memories")


# HNSW index for fast approximate nearest-neighbor search
# Much faster than exact search at scale (millions of vectors)
Index(
    "ix_memories_embedding_hnsw",
    Memory.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
