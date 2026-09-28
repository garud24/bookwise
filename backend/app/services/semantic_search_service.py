from sqlalchemy.orm import Session

from app.models.book import Book
from app.repositories.book_repository import search_books_by_embedding
from app.services.embedding_service import generate_embedding


async def semantic_search(
    db: Session,
    query: str,
    limit: int = 5
) -> list[Book]:

    query_embedding = await generate_embedding(query)

    return search_books_by_embedding(
        db,
        query_embedding,
        limit
    )