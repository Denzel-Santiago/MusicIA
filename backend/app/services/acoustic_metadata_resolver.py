from __future__ import annotations

from typing import Any

from app.services.acoustid_client import AcoustIDClient
from app.services.acoustic_identifier import (
    AcousticIdentifierError,
    rank_acoustic_candidates,
)
from app.services.musicbrainz_client import MusicBrainzClient


class AcousticMetadataResolverError(Exception):
    """Error durante la resolución acústica completa."""


def resolve_acoustic_metadata(
    acoustid_client: AcoustIDClient,
    musicbrainz_client: MusicBrainzClient,
    fingerprint: str,
    duration: float,
    local_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Resuelve la identidad musical mediante:

    fingerprint
        ↓
    AcoustID
        ↓
    múltiples candidatos
        ↓
    MusicBrainz
        ↓
    ranking de identidad
        ↓
    mejor candidato analizado

    No modifica SQLite.
    """

    if not fingerprint:
        raise AcousticMetadataResolverError(
            "No se proporcionó un fingerprint acústico."
        )

    if duration is None:
        raise AcousticMetadataResolverError(
            "La duración es necesaria para la resolución acústica."
        )

    if local_metadata is None:
        local_metadata = {
            "title": None,
            "artist": None,
            "duration": duration,
        }

    try:
        candidates = rank_acoustic_candidates(
            client=acoustid_client,
            musicbrainz_client=musicbrainz_client,
            local_metadata=local_metadata,
            fingerprint=fingerprint,
            duration=duration,
        )

    except AcousticIdentifierError as exc:
        raise AcousticMetadataResolverError(
            f"No se pudo realizar la identificación acústica: {exc}"
        ) from exc

    # No se encontraron candidatos acústicos.
    if not candidates:
        return {
            "status": "not_found",
            "acoustid": None,
            "acoustid_score": None,
            "musicbrainz_recording_id": None,
            "title": None,
            "artist": None,
            "duration": None,
            "candidate_score": None,
            "title_similarity": None,
            "artist_similarity": None,
            "duration_similarity": None,
            "candidates": [],
        }

    # Solamente los candidatos que MusicBrainz pudo analizar
    # pueden convertirse en una identidad válida.
    analyzed_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("status") == "analyzed"
        and candidate.get("final_score") is not None
    ]

    # AcoustID encontró candidatos, pero MusicBrainz no pudo
    # proporcionar información utilizable para ninguno.
    if not analyzed_candidates:
        return {
            "status": "musicbrainz_lookup_failed",
            "acoustid": None,
            "acoustid_score": None,
            "musicbrainz_recording_id": None,
            "title": None,
            "artist": None,
            "duration": None,
            "candidate_score": None,
            "title_similarity": None,
            "artist_similarity": None,
            "duration_similarity": None,
            "candidates": candidates,
        }

    # rank_acoustic_candidates() ya ordena los candidatos
    # analizados por SCORE FINAL descendente.
    best = analyzed_candidates[0]

    return {
        "status": "identified",
        "acoustid": best.get("acoustid"),
        "acoustid_score": best.get("acoustid_score"),
        "musicbrainz_recording_id": (
            best.get("musicbrainz_recording_id")
        ),
        "title": best.get("title"),
        "artist": best.get("artist"),
        "duration": best.get("duration"),
        "candidate_score": best.get("final_score"),
        "title_similarity": best.get("title_similarity"),
        "artist_similarity": best.get("artist_similarity"),
        "duration_similarity": best.get(
            "duration_similarity"
        ),
        "candidates": candidates,
    }
