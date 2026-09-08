from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database.connection import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(500), nullable=True)
    artist = Column(String(500), nullable=True)
    album = Column(String(500), nullable=True)
    genre = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)

    file_path = Column(String(2000), unique=True, nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)

    is_available = Column(Boolean, default=True, nullable=False)