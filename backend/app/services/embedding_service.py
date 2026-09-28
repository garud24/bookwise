import httpx
from app.models.book import Book

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

def build_book_embedding_text(book: Book) -> str:
    authors = ", ".join(book.authors or [])
    subjects = ", ".join(book.subjects or [])

    return (
        f"Title: {book.title}\n"
        f"Authors: {authors}\n"
        f"Description: {book.description or ''}\n"
        f"Subjects: {subjects}"
    )