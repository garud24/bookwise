import json
import httpx
from app.schemas.search import RerankedBook, RerankResponse
from app.services.semantic_search_service import semantic_search
from sqlalchemy.orm import Session

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"

async def test_qwen_structured():

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Return only JSON with these values: "
                    'id="TEST001", '
                    'title="Zathura", '
                    "score=0.95, "
                    'reason="Strong match for a space adventure."'
                )
            }
        ],
        "format": "json",
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_predict": 150
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
            timeout=120.0
        )

        response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]

    parsed = json.loads(content)

    return RerankedBook.model_validate(parsed)

async def rerank_books(
    db: Session,
    query: str,
    candidate_limit: int = 10,
    result_limit: int = 5
) -> RerankResponse:

    search_response = await semantic_search(
        db,
        query,
        candidate_limit
    )

    candidates = []

    for result in search_response.results:
        candidates.append({
            "id": result.id,
            "title": result.title,
            "authors": result.authors,
            "description": result.description,
            "subjects": result.subjects,
            "vector_distance": result.distance
        })

    prompt = f"""
You are a book recommendation reranker.

User request:
{query}

Candidate books:
{json.dumps(candidates, indent=2)}

Rerank these candidate books according to how well they match the user's request.

Return exactly {result_limit} recommendations.

For every recommendation return:
- id: the exact candidate book id
- title: the exact candidate title
- score: relevance score between 0 and 1
- reason: a concise explanation of why the book matches

Do not invent books.
Only use books from the candidate list.

Return JSON in this exact structure:
{{
    "query": "{query}",
    "recommendations": [
        {{
            "id": "...",
            "title": "...",
            "score": 0.0,
            "reason": "..."
        }}
    ]
}}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_predict": 1000
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
            timeout=120.0
        )

        response.raise_for_status()

    data = response.json()

    content = data["message"]["content"]

    parsed = json.loads(content)

    return RerankResponse.model_validate(parsed)