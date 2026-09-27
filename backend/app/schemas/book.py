from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    id: str
    title: str
    authors: list[str]
    description: str | None = None
    subjects: list[str] = Field(default_factory=list)
    first_publish_year: int | None = None
    cover_id: int | None = None