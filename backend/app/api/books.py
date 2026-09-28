from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.search import BookSearchRequest, BookSearchResponse, SemanticSearchResponse, BatchIngestionResponse
from app.services.book_service import search_open_library
from app.db.database import get_db
from app.services.semantic_search_service import semantic_search
from app.services.book_ingestion_service import ingest_and_process_books
from app.schemas.search import RerankResponse
from app.services.reranking_service import rerank_books

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

@router.post(
    "/ingest",
    response_model=BatchIngestionResponse
)
async def ingest_books(
    request: BookSearchRequest,
    db: Session = Depends(get_db)
):
    return await ingest_and_process_books(
        db,
        request.query,
        request.max_results
    )   

@router.post(
    "/recommend",
    response_model=RerankResponse
)
async def recommend_books(
    request: BookSearchRequest,
    db: Session = Depends(get_db)
):
    return await rerank_books(
        db=db,
        query=request.query,
        candidate_limit=10,
        result_limit=request.max_results
    )     