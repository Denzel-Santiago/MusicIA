"""Compatibility entry point for fingerprinting the stored library."""

from sqlalchemy.orm import Session

from app.adapters.audio.chromaprint.generator import ChromaprintGenerator
from app.adapters.persistence.sqlalchemy.song_repository import SQLAlchemySongRepository
from app.application.use_cases.fingerprinting import FingerprintLibrary


def fingerprint_library(db: Session) -> dict[str, int]:
    result = FingerprintLibrary(
        SQLAlchemySongRepository(db),
        ChromaprintGenerator(),
    ).execute()
    print("MusicAI - fingerprinting de biblioteca")
    print(f"Canciones pendientes: {result['total']}")
    print(f"Procesadas correctamente: {result['processed']}")
    print(f"Errores: {result['errors']}")
    return result
