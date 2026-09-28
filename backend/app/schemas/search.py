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