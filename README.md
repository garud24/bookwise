# BookWise AI

BookWise is a full-stack AI-powered book discovery and recommendation application that helps users find books using natural-language descriptions rather than traditional keyword search.

Instead of searching for an exact title, author, or genre, users can describe what they are in the mood for:

> "I want a mysterious adventure for a child who likes space."

BookWise converts that request into a semantic embedding, retrieves relevant books from PostgreSQL using vector similarity search, and then uses a locally running large language model to rerank the retrieved candidates and explain why each book matches the request.

The entire AI pipeline runs locally using open-source models through Ollama, while book metadata is sourced from Open Library.

---

## Features

- Natural-language book discovery
- Semantic search using vector embeddings
- PostgreSQL vector storage with pgvector
- LLM-based candidate reranking
- AI-generated recommendation explanations
- Structured LLM output validated with Pydantic
- Open Library book metadata ingestion
- Book description and subject enrichment
- Open Library cover integration
- Persistent local book catalog
- Idempotent book ingestion
- Batch ingestion and embedding generation
- FastAPI REST API
- React + TypeScript frontend
- Responsive AI recommendation dashboard
- Database schema migrations with Alembic
- Fully local LLM and embedding inference
- Dockerized PostgreSQL development environment

---

# Architecture

BookWise separates book ingestion from recommendation retrieval.

This allows books to be fetched, enriched, and embedded ahead of time so that recommendation requests operate against a persistent semantic catalog instead of repeatedly calling external APIs.

```text
                        BOOKWISE
                           │
              ┌────────────┴────────────┐
              │                         │
       DATA INGESTION              RECOMMENDATION
              │                         │
              ▼                         ▼
       Open Library API              User Query
              │                         │
              ▼                         ▼
       Search Results          nomic-embed-text
              │                         │
              ▼                         ▼
      PostgreSQL Books         Query Embedding
              │                         │
              ▼                         ▼
    Open Library Work API       pgvector Search
              │                         │
              ▼                         ▼
    Metadata Enrichment          Top-K Candidates
              │                         │
              ▼                         ▼
      Embedding Text             Qwen 3 Reranker
              │                         │
              ▼                         ▼
     nomic-embed-text       Structured Recommendations
              │                         │
              ▼                         ▼
      768-dim Embedding         Pydantic Validation
              │                         │
              ▼                         ▼
         PostgreSQL              FastAPI Response
          + pgvector                    │
                                        ▼
                                React / TypeScript UI
```

---

# System Components

## Frontend

**Technology**

- React
- TypeScript
- Vite
- CSS

The frontend provides a conversational discovery interface where users describe the kind of book they want.

It sends the natural-language request to:

```http
POST /api/books/recommend
```

and renders the returned recommendations including:

- book cover
- title
- author
- description
- AI match score
- AI-generated recommendation reason

The frontend does not perform recommendation logic itself. Its responsibility is limited to collecting user intent, calling the backend API, handling loading/error states, and presenting the structured response.

---

## Backend

**Technology**

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- HTTPX

FastAPI acts as the orchestration layer between:

- the React frontend
- PostgreSQL
- pgvector
- Open Library
- Ollama embedding models
- Ollama LLM inference

The backend is intentionally separated into API, service, repository, schema, model, and database layers.

```text
backend/
│
├── app/
│   ├── api/
│   │   └── books.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   ├── models/
│   │   └── book.py
│   │
│   ├── repositories/
│   │   └── book_repository.py
│   │
│   ├── schemas/
│   │   ├── book.py
│   │   └── search.py
│   │
│   ├── services/
│   │   ├── book_service.py
│   │   ├── book_ingestion_service.py
│   │   ├── embedding_service.py
│   │   ├── semantic_search_service.py
│   │   └── reranking_service.py
│   │
│   └── main.py
│
├── alembic/
├── alembic.ini
└── requirements.txt
```

Each layer has a distinct responsibility.

### API Layer

Defines HTTP endpoints and translates incoming requests into service calls.

### Service Layer

Contains application and orchestration logic such as:

- Open Library communication
- book ingestion
- metadata enrichment
- embedding generation
- semantic retrieval
- LLM reranking

### Repository Layer

Owns database operations and SQLAlchemy queries.

### Model Layer

Defines how application entities are persisted in PostgreSQL.

### Schema Layer

Defines API contracts using Pydantic.

This separation prevents HTTP handling, database queries, external API calls, and AI orchestration from becoming tightly coupled.

---

# Data Model

Books are stored persistently in PostgreSQL.

The primary book representation contains:

```text
Book
│
├── id
├── open_library_id
├── title
├── authors[]
├── description
├── subjects[]
├── first_publish_year
├── cover_id
└── embedding vector(768)
```

### `id`

Internal PostgreSQL primary key.

### `open_library_id`

Unique identifier corresponding to the Open Library Work.

This also provides an idempotency boundary during ingestion. Before inserting a book, BookWise checks whether the Open Library ID already exists.

### `authors`

Stored as a PostgreSQL array.

### `subjects`

Stores Open Library subject metadata and contributes semantic context when creating embeddings.

### `cover_id`

Open Library cover identifier used by the frontend to construct cover image URLs.

### `embedding`

A 768-dimensional vector generated by `nomic-embed-text`.

The column uses the PostgreSQL `vector` type provided by pgvector.

---

# Book Ingestion Pipeline

The recommendation engine requires a local semantic catalog before it can perform meaningful retrieval.

BookWise therefore provides a separate ingestion pipeline.

```text
Search Query
     │
     ▼
Open Library Search API
     │
     ▼
Normalize Search Results
     │
     ▼
Check Existing Book
     │
     ├──── Exists ────► Reuse Existing Record
     │
     └──── New ───────► Insert Book
                              │
                              ▼
                    Open Library Work API
                              │
                              ▼
                    Description + Subjects
                              │
                              ▼
                     Build Embedding Text
                              │
                              ▼
                      nomic-embed-text
                              │
                              ▼
                     768-dimensional Vector
                              │
                              ▼
                    PostgreSQL + pgvector
```

## 1. Search Open Library

BookWise calls the Open Library Search API using the user's ingestion query.

For example:

```text
fantasy adventure children
```

The search response provides basic metadata such as:

- Open Library Work ID
- title
- authors
- subjects
- first publication year
- cover ID

The external response is transformed into BookWise's internal schema before being persisted.

---

## 2. Idempotent Ingestion

Before creating a book, the ingestion service checks:

```text
Does this open_library_id already exist?
```

If yes:

```text
return existing book
```

If no:

```text
create new book
```

This prevents repeated ingestion requests from creating duplicate records.

Conceptually:

```text
Incoming book
      │
      ▼
Search by open_library_id
      │
   ┌──┴──┐
   │     │
 Found  Missing
   │     │
   ▼     ▼
 Reuse  Insert
```

---

# Metadata Enrichment

The Open Library Search API provides useful metadata, but richer semantic information can be obtained from the individual Work endpoint.

After persistence, BookWise retrieves the Work record and enriches the local book with information such as:

- description
- subjects

This enriched information improves the text representation used for embedding generation.

A simplified embedding document looks like:

```text
Title: Zathura

Authors:
Chris Van Allsburg

Description:
Two children discover a mysterious game that sends their house
into an extraordinary space adventure.

Subjects:
Juvenile Fiction, Space, Adventure, Fantasy
```

This is more semantically useful than embedding only:

```text
Zathura
```

because the embedding model now receives information about the book's meaning and themes.

---

# Embedding Generation

BookWise uses:

```text
nomic-embed-text
```

through a locally running Ollama instance.

The model converts text into a numerical representation:

```text
Book metadata
     │
     ▼
nomic-embed-text
     │
     ▼
[0.018, -0.032, 0.071, ...]
     │
     ▼
768 dimensions
```

An embedding represents semantic meaning in a multidimensional vector space.

Books with similar meaning should have vectors located closer together.

For example, these phrases use different words:

```text
"children exploring outer space"

"a young adventurer traveling among planets"
```

Traditional exact keyword matching may struggle because the words differ.

Semantic embeddings attempt to capture that both descriptions involve similar concepts.

---

# PostgreSQL + pgvector

BookWise uses PostgreSQL as both:

1. the primary relational database
2. the vector store

The pgvector extension adds vector data types and similarity operations to PostgreSQL.

The embedding column is:

```text
vector(768)
```

This corresponds to the dimensionality produced by `nomic-embed-text`.

This architecture avoids requiring a separate vector database for the project.

```text
PostgreSQL
│
├── Normal relational metadata
│   ├── title
│   ├── authors
│   ├── description
│   ├── subjects
│   └── cover_id
│
└── Vector metadata
    └── embedding vector(768)
```

The application can therefore retrieve normal metadata and perform semantic similarity search through the same database.

---

# Semantic Search

When a user asks:

```text
I want a mysterious adventure for a child who likes space
```

BookWise does **not** search PostgreSQL for those exact words.

Instead:

```text
User Query
     │
     ▼
nomic-embed-text
     │
     ▼
Query Vector
     │
     ▼
pgvector
     │
     ▼
Cosine Distance
     │
     ▼
Top-K Similar Books
```

The query and books use the **same embedding model**.

That is important because their vectors must exist in the same vector space for similarity comparison to be meaningful.

---

## Cosine Distance

BookWise currently performs retrieval using pgvector cosine distance.

Conceptually, cosine similarity measures the angle between two vectors.

For vectors `A` and `B`:

```text
cosine_similarity(A, B) =
          A · B
    -----------------
     ||A|| × ||B||
```

Cosine distance can be represented as:

```text
1 - cosine_similarity
```

Therefore, in the current retrieval implementation:

```text
smaller distance = stronger semantic match
```

For example:

```text
Book                         Distance
-------------------------------------
Zathura                      0.38
Captain Fact                 0.42
2001                         0.46
```

`Zathura` is considered the closest semantic match among these candidates.

The repository layer performs this search using pgvector through SQLAlchemy.

Conceptually:

```python
distance = Book.embedding.cosine_distance(query_embedding)

query.order_by(distance).limit(limit)
```

Only books with generated embeddings participate in semantic retrieval.

---

# Why Semantic Search Is Not Enough

Vector similarity is excellent for **candidate retrieval**, but the nearest vector is not always the best final recommendation.

Consider:

```text
"I want a mysterious adventure for a child who likes space."
```

Several books might be semantically related to:

- children
- adventure
- mystery
- fantasy
- space

But the user wants a book satisfying the combination of those preferences.

Embedding similarity gives BookWise an efficient shortlist.

The LLM then reasons over that shortlist.

This creates a two-stage architecture:

```text
                 All Books
                    │
                    ▼
            Semantic Retrieval
                    │
              Top-K Candidates
                    │
                    ▼
               LLM Reranking
                    │
                    ▼
          Final Recommendations
```

This pattern is commonly described as:

```text
Retrieve → Rerank
```

---

# LLM Reranking

BookWise uses:

```text
qwen3:4b
```

through Ollama.

The semantic search service first retrieves a candidate set.

The reranking service then provides those candidates to Qwen together with the original user query.

Conceptually:

```text
User request
+
Candidate 1
Candidate 2
Candidate 3
...
Candidate N
       │
       ▼
     Qwen
       │
       ▼
Reordered candidates
+
match scores
+
recommendation reasons
```

The LLM is **not allowed to search the entire catalog**.

pgvector performs retrieval first.

This keeps responsibilities separate:

```text
nomic-embed-text
        │
        └── Represents semantic meaning

pgvector
        │
        └── Retrieves relevant candidates

Qwen
        │
        └── Reasons about and reranks candidates
```

---

# Preventing LLM Metadata Hallucination

An important design decision in BookWise is that the LLM is not treated as the source of truth for book metadata.

Qwen is responsible for generating only recommendation-related information:

```text
id
title
score
reason
```

The backend remains responsible for trusted metadata:

```text
authors
description
cover_id
```

After Qwen returns its ranking, BookWise creates a lookup from the semantic-search candidates:

```text
candidate ID
      │
      ▼
Trusted candidate metadata
```

Then the final response is assembled by combining:

```text
LLM-owned information
├── score
└── reason

Backend-owned information
├── id
├── title
├── authors
├── description
└── cover_id
```

This creates an important trust boundary.

The LLM can explain and rank books, but it cannot independently invent the author, cover ID, or description returned by the API.

---

# Structured LLM Output

LLMs naturally generate free-form text.

That is inconvenient for production APIs because the application expects predictable data.

Instead of accepting arbitrary text such as:

```text
I think you would really enjoy Zathura because...
```

BookWise instructs Qwen to return JSON resembling:

```json
{
  "query": "mysterious space adventure",
  "recommendations": [
    {
      "id": "OL3743761W",
      "title": "Zathura",
      "score": 0.92,
      "reason": "A strong match for a child looking for a mysterious space adventure."
    }
  ]
}
```

The response is then validated using Pydantic.

The flow is:

```text
Qwen
 │
 ▼
JSON String
 │
 ▼
json.loads()
 │
 ▼
Python Dictionary
 │
 ▼
Pydantic Validation
 │
 ▼
Typed Application Object
```

This is important because an LLM response should be treated as **untrusted external input**, even when the model runs locally.

---

# Pydantic Schemas

Pydantic defines the contracts between different parts of BookWise.

For example, semantic retrieval returns data conceptually similar to:

```python
class SemanticSearchResult(BaseModel):
    id: str
    title: str
    authors: list[str]
    description: str | None
    subjects: list[str]
    cover_id: int | None
    distance: float
```

The final recommendation object contains:

```python
class RerankedBook(BaseModel):
    id: str
    title: str
    authors: list[str]
    description: str | None
    cover_id: int | None
    score: float
    reason: str
```

The distinction is intentional.

Semantic search cares about:

```text
distance
```

while the final recommendation API cares about:

```text
score
reason
```

Schemas therefore represent the contract needed at each stage rather than exposing database objects directly.

---

# Complete Recommendation Request Flow

This is the main runtime path of BookWise.

```text
1. USER
   │
   │ "I want a mysterious adventure
   │  for a child who likes space"
   │
   ▼
2. REACT
   │
   │ POST /api/books/recommend
   │
   ▼
3. FASTAPI
   │
   ▼
4. RERANKING SERVICE
   │
   ▼
5. SEMANTIC SEARCH SERVICE
   │
   ▼
6. EMBEDDING SERVICE
   │
   │ User query
   │
   ▼
7. OLLAMA
   │ nomic-embed-text
   │
   ▼
8. QUERY EMBEDDING
   │ 768 dimensions
   │
   ▼
9. BOOK REPOSITORY
   │
   ▼
10. POSTGRESQL + PGVECTOR
   │
   │ cosine distance
   │
   ▼
11. TOP-K BOOKS
   │
   ▼
12. RERANKING SERVICE
   │
   │ Query + candidate metadata
   │
   ▼
13. OLLAMA
   │ qwen3:4b
   │
   ▼
14. STRUCTURED JSON
   │
   ▼
15. PYDANTIC VALIDATION
   │
   ▼
16. TRUSTED METADATA MERGE
   │
   ▼
17. FASTAPI RESPONSE
   │
   ▼
18. REACT
   │
   ▼
19. BOOK CARDS
```

The important architectural idea is that BookWise is not simply:

```text
User → LLM → Answer
```

It is:

```text
User
 ↓
Embedding Model
 ↓
Vector Retrieval
 ↓
Candidate Set
 ↓
LLM Reranking
 ↓
Schema Validation
 ↓
Trusted Metadata Merge
 ↓
Structured API
 ↓
UI
```

---

# API Endpoints

## Search Books

```http
POST /api/books/search
```

Searches Open Library for books.

Example request:

```json
{
  "query": "space adventure children",
  "max_results": 5
}
```

This endpoint primarily represents the external book discovery layer.

---

## Ingest Books

```http
POST /api/books/ingest
```

Runs the ingestion pipeline:

```text
Open Library Search
        ↓
Persistence
        ↓
Metadata Enrichment
        ↓
Embedding Generation
        ↓
Vector Storage
```

Example request:

```json
{
  "query": "mystery detective children",
  "max_results": 5
}
```

The batch operation reports processing results such as:

```json
{
  "query": "mystery detective children",
  "requested": 5,
  "found": 5,
  "processed": 5,
  "failed": 0,
  "failures": []
}
```

Individual book failures are isolated so that one failed enrichment or embedding request does not necessarily invalidate the entire batch.

---

## Semantic Search

```http
POST /api/books/semantic-search
```

Embeds the user's query and retrieves semantically similar books from PostgreSQL using pgvector.

This endpoint exposes the retrieval stage independently from LLM reranking, which is useful for debugging and evaluating semantic search quality.

---

## Recommend Books

```http
POST /api/books/recommend
```

Runs the complete recommendation pipeline:

```text
Query
 ↓
Embedding
 ↓
Semantic Search
 ↓
Top-K Candidates
 ↓
Qwen Reranking
 ↓
Pydantic Validation
 ↓
Metadata Merge
 ↓
Final Recommendations
```

The frontend primarily communicates with this endpoint.

---

# Batch Processing and Failure Isolation

Book ingestion involves multiple operations that can fail independently:

- Open Library request
- metadata enrichment
- Ollama embedding request
- database transaction

BookWise processes individual books independently during batch ingestion.

Conceptually:

```python
for book in books:
    try:
        enrich_book()
        generate_embedding()
        persist_changes()
    except Exception:
        rollback()
        record_failure()
```

This means a failure processing one book does not automatically stop the remaining books from being processed.

The batch response records:

```text
requested
found
processed
failed
failures
```

This makes ingestion behavior observable to API consumers.

---

# Database Transactions

SQLAlchemy sessions are created per request using a dependency.

Conceptually:

```python
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
```

The FastAPI dependency lifecycle therefore manages session cleanup.

Repository operations commit changes when appropriate.

When an individual batch operation fails:

```python
db.rollback()
```

returns the SQLAlchemy session to a usable transaction state before processing continues.

---

# Database Migrations

BookWise uses Alembic to version database schema changes.

For example, adding semantic search required adding:

```text
embedding vector(768)
```

to the books table.

Instead of manually modifying every environment, Alembic records schema evolution as migrations.

Typical workflow:

```bash
alembic revision --autogenerate -m "add book embeddings"
alembic upgrade head
```

This separates:

```text
Application Model
```

from:

```text
Database Schema History
```

and makes schema changes reproducible.

---

# External Services

## Open Library

Open Library provides:

- book search
- Work metadata
- descriptions
- subjects
- authors
- publication metadata
- cover IDs
- book cover images

BookWise persists relevant metadata locally so recommendation requests do not need to depend on Open Library for every operation.

---

## Ollama

Ollama runs the AI models locally.

BookWise currently uses two different models because they perform different jobs.

### `nomic-embed-text`

Used for:

```text
Text → Vector
```

Responsibilities:

- book embeddings
- user query embeddings

### `qwen3:4b`

Used for:

```text
Candidates + User Intent → Ranked Recommendations
```

Responsibilities:

- reasoning about candidate relevance
- reranking
- match scoring
- recommendation explanations

This separation is important:

**Embedding models retrieve. LLMs reason.**

---

# Error Handling

BookWise distinguishes several Open Library failure modes.

Examples include:

```text
Timeout
    → 504 Gateway Timeout

Open Library HTTP error
    → 502 Bad Gateway

Connection/request failure
    → 503 Service Unavailable
```

This is preferable to converting every external-service failure into a generic `500 Internal Server Error`.

The frontend also handles recommendation request failures and displays an error state instead of silently failing.

---

# CORS

The frontend and backend run on different local origins during development.

For example:

```text
Frontend:
http://localhost:5173

Backend:
http://127.0.0.1:8000
```

Because browsers enforce the same-origin policy, FastAPI configures CORS for the frontend development origins.

This allows the React application to make API requests to FastAPI while still keeping explicit control over permitted origins.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python |
| API Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL 17 |
| Vector Search | pgvector |
| Database Migrations | Alembic |
| HTTP Client | HTTPX |
| Embeddings | nomic-embed-text |
| LLM | Qwen3 4B |
| Local AI Runtime | Ollama |
| Book Data | Open Library |
| Database Runtime | Docker / Docker Compose |

---

# Local Development Setup

## Prerequisites

Install:

- Python
- Node.js
- Docker
- Ollama

The project was developed using:

```text
Python 3.14
PostgreSQL 17
Ollama
Node.js
```

---

## 1. Clone the Repository

```bash
git clone <repository-url>
cd bookwise
```

---

## 2. Start PostgreSQL

BookWise uses PostgreSQL with pgvector support through Docker.

Start the database:

```bash
docker compose up -d
```

Verify the container:

```bash
docker ps
```

The development database uses:

```text
Database: bookwise
User:     bookwise
Port:     5432
```

---

## 3. Configure the Backend

Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Create:

```text
.env
```

with:

```env
DATABASE_URL=postgresql+psycopg://bookwise:bookwise@localhost:5432/bookwise
```

The `.env` file should not be committed to source control.

A repository-safe `.env.example` can contain the expected variable structure.

---

## 4. Apply Database Migrations

From the backend directory:

```bash
cd backend
alembic upgrade head
```

This creates or updates the database schema to the latest migration.

---

## 5. Install the Local AI Models

Pull the embedding model:

```bash
ollama pull nomic-embed-text
```

Pull the reranking model:

```bash
ollama pull qwen3:4b
```

Verify Ollama is running:

```bash
ollama list
```

---

## 6. Start the Backend

From the backend directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 7. Populate the Book Catalog

Before semantic search can return useful results, books must exist locally with generated embeddings.

Using Swagger or an API client, call:

```http
POST /api/books/ingest
```

with queries such as:

```json
{
  "query": "fantasy adventure children",
  "max_results": 20
}
```

Additional categories can be ingested to increase catalog diversity.

For example:

```text
space science fiction children
mystery detective children
fantasy magic adventure
classic children's literature
```

---

## 8. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will start the frontend, typically at:

```text
http://localhost:5173
```

---

# Example End-to-End Request

A user enters:

```text
I want a mysterious adventure for a child who likes space.
```

### Step 1 — React

React sends:

```json
{
  "query": "I want a mysterious adventure for a child who likes space",
  "max_results": 5
}
```

to:

```http
POST /api/books/recommend
```

### Step 2 — Query Embedding

`nomic-embed-text` converts the query into a 768-dimensional vector.

### Step 3 — Candidate Retrieval

pgvector compares the query vector against stored book vectors using cosine distance.

The closest candidates are returned.

### Step 4 — Reranking

The candidate metadata and original request are sent to `qwen3:4b`.

Qwen evaluates the candidates against the complete user intent.

### Step 5 — Validation

The LLM JSON response is parsed and validated using Pydantic.

### Step 6 — Trusted Metadata

The backend joins the LLM ranking with trusted candidate metadata using Open Library IDs.

### Step 7 — API Response

FastAPI returns structured recommendations.

### Step 8 — UI

React displays:

- cover
- ranking
- AI match score
- title
- author
- description
- explanation

---

# Important Engineering Decisions

## Why PostgreSQL + pgvector instead of a separate vector database?

BookWise already requires relational persistence for book metadata.

pgvector allows both relational data and embeddings to live in PostgreSQL:

```text
One database
├── transactional metadata
└── semantic vectors
```

For the current scale, this keeps the architecture simpler while still providing real vector retrieval.

---

## Why retrieve before calling the LLM?

Sending every stored book to an LLM would become increasingly:

- slow
- expensive in context size
- difficult to scale
- noisy for ranking

Instead:

```text
Database
   ↓
Fast semantic retrieval
   ↓
Small candidate set
   ↓
More expensive LLM reasoning
```

The expensive reasoning stage therefore operates only on candidates likely to be relevant.

---

## Why use the same embedding model for books and queries?

Similarity only makes sense when both vectors are represented in the same embedding space.

Therefore:

```text
Books → nomic-embed-text
Queries → nomic-embed-text
```

Changing the embedding model would require regenerating the stored book embeddings before comparing them with vectors from the new model.

---

## Why store embeddings?

Generating embeddings during every recommendation request would repeatedly perform identical work for static books.

Instead:

```text
Book ingestion
      ↓
Generate embedding once
      ↓
Persist vector
      ↓
Reuse during searches
```

Only the user's query needs a new embedding for each recommendation request.

---

## Why separate semantic search and reranking?

They solve different problems.

Semantic search answers:

> Which books are broadly related to this query?

Reranking answers:

> Among those books, which candidates best satisfy the user's complete request?

Separating the stages also makes each component independently testable.

---

## Why validate LLM responses?

An LLM does not guarantee application correctness.

Even with JSON mode and explicit instructions, model output should be treated as external input.

Pydantic provides a boundary:

```text
Untrusted model output
        ↓
Schema validation
        ↓
Application-safe structure
```

---

## Why keep trusted metadata outside the LLM?

Book metadata already exists in the database.

There is no reason to ask the model to recreate facts such as:

```text
author
description
cover ID
```

Doing so introduces unnecessary hallucination risk.

The LLM therefore performs the task for which it is useful — reasoning about relevance — while the application remains authoritative for stored facts.

---

# Current Limitations

BookWise is currently an MVP and has several known areas for improvement.

## Local LLM Latency

Qwen3 4B runs locally and recommendation generation can take significantly longer than the vector retrieval stage.

This is currently accepted as an MVP tradeoff in exchange for:

- no paid inference API
- local execution
- no external LLM dependency
- simple development setup

Potential improvements include:

- reducing reranking candidate count
- shortening candidate metadata
- limiting description length
- reducing generation length
- caching repeated recommendations
- using a smaller/faster reranking model
- separating ranking from explanation generation

---

## Vector Search Indexing

The current catalog is small enough that exact vector retrieval is sufficient.

At larger scale, an approximate nearest-neighbor index such as HNSW could reduce vector search latency.

The architecture could evolve from:

```text
Exact vector scan
```

to:

```text
HNSW approximate nearest-neighbor search
```

without replacing PostgreSQL.

---

## Recommendation Scoring

The current AI match score is produced during the LLM reranking stage.

A future version could combine multiple signals:

```text
Final Score =
    vector relevance
  + LLM relevance
  + metadata relevance
```

This could make ranking more deterministic and reduce reliance on a single LLM-generated score.

---

## Catalog Size

Recommendation quality is bounded by the books already ingested into PostgreSQL.

The LLM reranks retrieved books; it does not independently discover arbitrary books outside the local candidate catalog during recommendation.

A larger and more diverse ingestion corpus would improve recommendation coverage.

---

# Future Improvements

Potential production-oriented improvements include:

### Retrieval

- HNSW vector index
- hybrid keyword + semantic search
- metadata filters
- genre filtering
- publication-year filtering
- vector/LLM score fusion

### AI

- prompt versioning
- reranking evaluation dataset
- smaller specialized reranker
- response caching
- model abstraction layer
- configurable local models

### Backend

- asynchronous job processing for ingestion
- background embedding generation
- centralized exception handling
- structured logging
- request tracing
- metrics
- rate limiting

### Database

- larger catalog
- optimized vector indexes
- ingestion timestamps
- embedding model/version metadata
- embedding regeneration workflows

### Testing

- repository unit tests
- service tests
- mocked Open Library tests
- mocked Ollama tests
- API integration tests
- end-to-end recommendation tests

### Deployment

- backend containerization
- frontend containerization
- reverse proxy
- production PostgreSQL
- CI/CD
- health checks
- monitoring

---

# Concepts Demonstrated

BookWise demonstrates several backend and AI engineering concepts in one application:

**Backend engineering**

- REST API design
- layered architecture
- dependency injection
- repository pattern
- database transactions
- external API integration
- failure isolation
- error handling
- CORS

**Database engineering**

- PostgreSQL
- relational modeling
- uniqueness constraints
- schema migrations
- SQLAlchemy ORM
- vector columns
- similarity queries

**AI engineering**

- embeddings
- semantic search
- vector databases
- cosine distance
- retrieve-and-rerank architecture
- local LLM inference
- prompt orchestration
- structured LLM output
- schema validation
- hallucination boundaries

**Frontend engineering**

- React
- TypeScript
- API integration
- asynchronous UI state
- loading states
- error states
- responsive design
- external image integration

---

# Key Architectural Takeaway

BookWise is intentionally designed so that each technology performs the job it is best suited for.

```text
Open Library
    │
    └── Source of book information

PostgreSQL
    │
    └── Persistent source of truth

nomic-embed-text
    │
    └── Converts meaning into vectors

pgvector
    │
    └── Efficiently retrieves semantic candidates

Qwen
    │
    └── Reasons about candidate relevance

Pydantic
    │
    └── Enforces application contracts

FastAPI
    │
    └── Orchestrates the system

React
    │
    └── Presents the experience to the user
```

The core principle is:

> **Use retrieval to narrow the search space, use the LLM to reason over that search space, and keep the application/database authoritative for factual metadata.**

---

# Project Status

BookWise currently supports a complete end-to-end recommendation workflow:

```text
Open Library
     ↓
Book ingestion
     ↓
Metadata enrichment
     ↓
Embedding generation
     ↓
PostgreSQL + pgvector
     ↓
Natural-language query
     ↓
Semantic retrieval
     ↓
Qwen reranking
     ↓
Structured validation
     ↓
React recommendation experience
```

The current version is designed as a local-first AI application and does not require a paid LLM or embedding API.

---

## License

This project is intended for educational and portfolio use.
