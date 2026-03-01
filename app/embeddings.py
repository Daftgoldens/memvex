from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed(text: str) -> list[float]:
    """Embed a single text string. Returns a list of floats."""
    client = get_openai_client()
    text = text.replace("\n", " ").strip()
    response = await client.embeddings.create(
        input=text,
        model=settings.embedding_model,
    )
    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in a single API call (cheaper + faster)."""
    client = get_openai_client()
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    response = await client.embeddings.create(
        input=cleaned,
        model=settings.embedding_model,
    )
    # Response is sorted by index
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
