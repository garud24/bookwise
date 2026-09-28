from sqlalchemy.orm import Session

from app.models.book import Book
from app.repositories.book_repository import search_books_by_embedding
from app.services.embedding_service import generate_embedding
from app.schemas.search import (
    SemanticSearchResult,
    SemanticSearchResponse,
)

async def semantic_search(
    db: Session,
    query: str,
    limit: int = 5
) -> SemanticSearchResponse:

    query_embedding = await generate_embedding(query)

    rows = search_books_by_embedding(
        db,
        query_embedding,
        limit
    )

    results = []

    for book, distance in rows:
        result = SemanticSearchResult(
            id=book.open_library_id,
            title=book.title,
            authors=book.authors,
            description=book.description,
            subjects=book.subjects,
            cover_id=book.cover_id,
            distance=distance
        )

        results.append(result)

    return SemanticSearchResponse(
        query=query,
        results=results
    )