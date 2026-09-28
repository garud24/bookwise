from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
from pgvector.sqlalchemy import Vector

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    open_library_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    authors: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False
    )
    
    description: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
    )
    
    subjects: Mapped[list[str]] = mapped_column(
    ARRAY(String),
    nullable=False
    )

    first_publish_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    cover_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    
    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(768),
    nullable=True
    )
    