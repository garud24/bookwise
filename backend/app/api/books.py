from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.search import BookSearchRequest, BookSearchResponse, SemanticSearchResponse
from app.services.book_service import search_open_library
from app.db.database import get_db
from app.services.semantic_search_service import semantic_search

router = APIRouter()


@router.post("/search", response_model=BookSearchResponse)
async def search_books(request: BookSearchRequest):
    result = await search_open_library(
        request.query,
        request.max_results
    )

    return result

@router.post(
    "/semantic-search",
    response_model=SemanticSearchResponse
)
async def search_books_semantically(
    request: BookSearchRequest,
    db: Session = Depends(get_db)
):
    return await semantic_search(
        db,
        request.query,
        request.max_results
    )