from pydantic import BaseModel, Field
from app.schemas.book import BookResponse

class BookSearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=20)
    
class BookSearchResponse(BaseModel):
    query: str
    total_found: int
    books: list[BookResponse]   