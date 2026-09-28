from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book

def get_book_by_open_library_id(
    db: Session,
    open_library_id: str
) -> Book | None:

    statement = select(Book).where(
        Book.open_library_id == open_library_id
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()

def save_book(
    db: Session,
    book: Book
) -> Book:

    db.add(book)
    db.commit()
    db.refresh(book)

    return book

def update_book_metadata(
    db: Session,
    book: Book,
    description: str | None,
    subjects: list[str]
) -> Book:

    book.description = description
    book.subjects = subjects

    db.commit()
    db.refresh(book)

    return book