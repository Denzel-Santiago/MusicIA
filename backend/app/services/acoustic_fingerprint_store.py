from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.song import Song
from app.services.acoustic_fingerprint import (
    generate_fingerprint,
)


class AcousticFingerprintStoreError(Exception):
    """Error al guardar un fingerprint acústico."""


def generate_and_store_fingerprint(
    db: Session,
    song: Song,
) -> Song:
    """
    Genera el fingerprint acústico del archivo de una canción
    y lo guarda en el registro existente de SQLite.
    """

    try:
        result = generate_fingerprint(song.file_path)
    except Exception as exc:
        raise AcousticFingerprintStoreError(
            f"No se pudo generar el fingerprint para "
            f"'{song.file_path}': {exc}"
        ) from exc

    fingerprint = result["fingerprint"]

    if not fingerprint:
        raise AcousticFingerprintStoreError(
            "El fingerprint generado está vacío."
        )

    song.acoustic_fingerprint = fingerprint

    try:
        db.commit()
        db.refresh(song)
    except Exception as exc:
        db.rollback()
        raise AcousticFingerprintStoreError(
            f"No se pudo guardar el fingerprint en SQLite: {exc}"
        ) from exc

    return song