from pydantic import BaseModel, Field
from app.schemas.book import BookResponse

class BookSearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=20)
    
class BookSearchResponse(BaseModel):
    query: str
    total_found: int
    books: list[BookResponse]   

class SemanticSearchResult(BaseModel):
    id: str
    title: str
    authors: list[str]
    description: str | None = None
    subjects: list[str]
    distance: float


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult] 

class BatchFailure(BaseModel):
    open_library_id: str
    title: str
    error: str


class BatchIngestionResponse(BaseModel):
    query: str
    requested: int
    found: int
    processed: int
    failed: int
    failures: list[BatchFailure]   

class RerankedBook(BaseModel):
    id: str
    title: str
    score: float
    reason: str


class RerankResponse(BaseModel):
    query: str
    recommendations: list[RerankedBook]        