from fastapi import APIRouter

from app.schemas.search import BookSearchRequest, BookSearchResponse
from app.services.book_service import search_open_library

router = APIRouter()


@router.post("/search", response_model=BookSearchResponse)
async def search_books(request: BookSearchRequest):
    result = await search_open_library(
        request.query,
        request.max_results
    )

    return result