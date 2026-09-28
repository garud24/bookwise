from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.book import BookResponse
from app.repositories.book_repository import (
    get_book_by_open_library_id,
    save_book,
)
from app.repositories.book_repository import (
    get_book_by_open_library_id,
    save_book,
    update_book_metadata,
)

from app.services.book_service import (
    search_open_library,
    get_open_library_work,
    extract_description,
)

from app.services.embedding_service import (
    build_book_embedding_text,
    generate_embedding,
)

from app.repositories.book_repository import update_book_embedding

def ingest_book(
    db: Session,
    book_response: BookResponse
) -> Book:

    existing_book = get_book_by_open_library_id(
        db,
        book_response.id
    )

    if existing_book:
        return existing_book

    book = Book(
        open_library_id=book_response.id,
        title=book_response.title,
        authors=book_response.authors,
        description=book_response.description,
        subjects=book_response.subjects,
        first_publish_year=book_response.first_publish_year,
        cover_id=book_response.cover_id
    )

    return save_book(db, book)

async def ingest_search_results(
    db: Session,
    query: str,
    limit: int
) -> list[Book]:

    search_response = await search_open_library(
        query,
        limit
    )

    saved_books = []

    for book_response in search_response.books:
        saved_book = ingest_book(
            db,
            book_response
        )

        saved_books.append(saved_book)

    return saved_books

async def enrich_book(
    db: Session,
    open_library_id: str
) -> Book | None:

    book = get_book_by_open_library_id(
        db,
        open_library_id
    )

    if not book:
        return None

    work = await get_open_library_work(
        open_library_id
    )

    description = extract_description(work)

    subjects = work.get("subjects", [])

    return update_book_metadata(
        db,
        book,
        description,
        subjects
    )  

async def embed_book(
    db: Session,
    open_library_id: str
) -> Book | None:

    book = get_book_by_open_library_id(
        db,
        open_library_id
    )

    if not book:
        return None

    embedding_text = build_book_embedding_text(book)

    embedding = await generate_embedding(
        embedding_text
    )

    return update_book_embedding(
        db,
        book,
        embedding
    )

async def enrich_and_embed_book(
    db: Session,
    open_library_id: str
) -> Book | None:

    book = await enrich_book(
        db,
        open_library_id
    )

    if not book:
        return None

    return await embed_book(
        db,
        open_library_id
    )      

async def ingest_and_process_books(
    db: Session,
    query: str,
    limit: int = 20
) -> list[Book]:

    books = await ingest_search_results(
        db,
        query,
        limit
    )

    processed_books = []

    for book in books:
        try:
            
            processed_book = await enrich_and_embed_book(
                db,
                book.open_library_id
            )

            if processed_book:
                processed_books.append(processed_book)
        except Exception as exc:
            db.rollback()
            print(
                f"Failed to process "
                f"{book.open_library_id} "
                f"({book.title}): {exc}"
            )
                    

    return processed_books    