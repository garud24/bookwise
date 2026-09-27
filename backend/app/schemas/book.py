from pydantic import BaseModel


class BookResponse(BaseModel):
    id: str
    title: str
    authors: list[str]
    first_publish_year: int | None = None
    cover_id: int | None = None