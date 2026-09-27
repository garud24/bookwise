import httpx
from fastapi import HTTPException
from app.schemas.book import BookResponse
from app.schemas.search import BookSearchResponse


async def search_open_library(query: str, limit: int):
    url = "https://openlibrary.org/search.json"

    params = {
        "q": query,
        "limit": limit
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=10.0
            )
        response.raise_for_status()
    except httpx.TimeoutException:
        print("Open Library request timed out")
        raise HTTPException(
            status_code=504,
            detail="Open Library request timed out."
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="Open Library returned an error."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Open Library."
        )
    data = response.json()
    total_found = data["numFound"]

    books = []

    for book in data["docs"]:
        transformed_book = transform_book(book)
        books.append(transformed_book)

    return BookSearchResponse(
        query=query,
        total_found=total_found,
        books=books
    )


def transform_book(book: dict):
    return BookResponse(
        id=book["key"].replace("/works/", ""),
        title=book["title"],
        authors=book.get("author_name", []),
        first_publish_year=book.get("first_publish_year"),
        cover_id=book.get("cover_i")
    )