from fastapi import FastAPI, HTTPException
from app.api.books import router as book_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get('/health')
def get_health():
    return {"status":"healthy"}

app.include_router(
    book_router,
    prefix="/api/books",
    tags=["Books"]
)
