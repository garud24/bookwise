import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Load environment variables from .env
load_dotenv()

# Read the database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Fail immediately if DATABASE_URL is missing
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        
class Base(DeclarativeBase):
    pass