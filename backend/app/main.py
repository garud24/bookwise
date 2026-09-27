from fastapi import FastAPI, HTTPException
from app.api.books import router as book_router

app = FastAPI()

@app.get('/health')
def get_health():
    return {"status":"healthy"}

app.include_router(
    book_router,
    prefix="/api/books",
    tags=["Books"]
)
