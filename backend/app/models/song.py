from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database.connection import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)

    # Metadata original
    title = Column(String(500), nullable=True)
    artist = Column(String(500), nullable=True)
    album = Column(String(500), nullable=True)
    genre = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)

    # Metadata interpretada por MusicAI
    normalized_title = Column(String(500), nullable=True)
    normalized_artist = Column(String(500), nullable=True)
    metadata_source = Column(String(100), nullable=True)
    metadata_confidence = Column(Float, nullable=True)

    # Archivo
    file_path = Column(String(2000), unique=True, nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    acoustic_fingerprint = Column(String(10000), unique=True, nullable=True, index=True)

    # Disponibilidad
    is_available = Column(Boolean, default=True, nullable=False)