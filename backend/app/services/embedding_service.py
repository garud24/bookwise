import httpx


OLLAMA_EMBEDDING_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"


async def generate_embedding(text: str) -> list[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_EMBEDDING_URL,
            json=payload,
            timeout=30.0
        )

        response.raise_for_status()

    data = response.json()

    return data["embeddings"][0]