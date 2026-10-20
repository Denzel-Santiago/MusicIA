"""Compatibility facade for fingerprint persistence."""

from sqlalchemy.orm import Session

from app.adapters.audio.chromaprint.generator import ChromaprintGenerator
from app.adapters.persistence.sqlalchemy.song_repository import SQLAlchemySongRepository
from app.application.use_cases.fingerprinting import (
    FingerprintStorageError as AcousticFingerprintStoreError,
    GenerateAndStoreFingerprint,
)
from app.adapters.persistence.sqlalchemy.song import Song


def generate_and_store_fingerprint(db: Session, song: Song) -> Song:
    repository = SQLAlchemySongRepository(db)
    record = repository.find_by_id(song.id)
    if record is None:
        raise AcousticFingerprintStoreError(f"No existe la canción con id {song.id}.")
    GenerateAndStoreFingerprint(repository, ChromaprintGenerator()).execute(record)
    return song


__all__ = ["AcousticFingerprintStoreError", "generate_and_store_fingerprint"]
