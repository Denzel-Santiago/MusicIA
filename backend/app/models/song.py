from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    artist: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    album: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    genre: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    file_path: Mapped[str] = mapped_column(
        String(2000),
        unique=True,
        nullable=False
    )