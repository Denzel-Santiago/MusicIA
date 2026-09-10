"""Identificación de canciones usando metadata local y fuentes externas."""

from __future__ import annotations

from app.services.metadata_matcher import rank_candidates
from app.services.metadata_resolver import resolve_metadata
from app.services.musicbrainz_client import create_musicbrainz_client


IDENTIFICATION_SOURCE = "local"
EXTERNAL_IDENTIFICATION_SOURCE = "musicbrainz"


def _first_available(metadata, normalized_key, original_key):
    return metadata.get(normalized_key) or metadata.get(original_key)


def _status_and_confidence(title, artist):
    if title and artist:
        return "identified", 0.9

    if title:
        return "partial", 0.5

    if artist:
        return "partial", 0.4

    return "unidentified", 0.0


def identify_song(metadata):
    """
    Identificación básica usando únicamente la metadata local.

    Esta función no realiza consultas externas.
    """
    title = _first_available(
        metadata,
        "normalized_title",
        "title",
    )

    artist = _first_available(
        metadata,
        "normalized_artist",
        "artist",
    )

    status, confidence = _status_and_confidence(
        title,
        artist,
    )

    return {
        "title": title,
        "artist": artist,
        "album": metadata.get("album"),
        "year": metadata.get("year"),
        "duration": metadata.get("duration"),
        "confidence": confidence,
        "source": IDENTIFICATION_SOURCE,
        "status": status,
        "external_ids": {},
    }


def _should_verify_externally(resolved_metadata):
    """
    Decide si MusicAI debería intentar verificar la identidad
    mediante una fuente externa.

    La decisión considera tanto la calidad de la metadata
    como la confianza de la resolución realizada por MusicAI.
    """

    quality = resolved_metadata.get("quality", {})

    quality_status = quality.get("status")
    quality_confidence = quality.get("confidence", 0.0)

    resolution_status = resolved_metadata.get(
        "resolution_status"
    )

    metadata_confidence = resolved_metadata.get(
        "metadata_confidence",
        0.0,
    )

    title = resolved_metadata.get("title")
    artist = resolved_metadata.get("artist")

    # ---------------------------------------------------------
    # 1. Metadata sospechosa
    # ---------------------------------------------------------
    # No queremos enviar información posiblemente contaminada
    # a MusicBrainz.
    if quality_status == "suspicious":
        return {
            "needed": True,
            "query_ready": False,
            "reason": "suspicious_metadata",
        }

    # ---------------------------------------------------------
    # 2. Identificación completa y confiable
    # ---------------------------------------------------------
    # Si MusicAI pudo obtener artista + título con alta
    # confianza, podemos utilizar la identificación local.
    #
    # Esto incluye casos como:
    #
    # Avicii - The Nights.mp3
    #
    # aunque la metadata original no tuviera artista.
    if (
        resolution_status == "resolved"
        and title
        and artist
        and metadata_confidence >= 0.8
    ):
        return {
            "needed": False,
            "query_ready": False,
            "reason": "local_resolution_sufficient",
        }

    # ---------------------------------------------------------
    # 3. Identificación completa pero de confianza moderada
    # ---------------------------------------------------------
    if (
        resolution_status == "resolved"
        and title
        and artist
    ):
        if metadata_confidence >= 0.6:
            return {
                "needed": True,
                "query_ready": True,
                "reason": "moderate_resolution_confidence",
            }

        return {
            "needed": True,
            "query_ready": True,
            "reason": "low_resolution_confidence",
        }

    # ---------------------------------------------------------
    # 4. Identificación incompleta
    # ---------------------------------------------------------
    if resolution_status != "resolved":

        # Tenemos ambos datos aunque el resolver no los haya
        # considerado suficientemente confiables.
        if title and artist:
            return {
                "needed": True,
                "query_ready": True,
                "reason": "incomplete_resolution_with_artist_title",
            }

        # Solo tenemos título o solo artista.
        if title or artist:
            return {
                "needed": True,
                "query_ready": False,
                "reason": "insufficient_local_data",
            }

        return {
            "needed": True,
            "query_ready": False,
            "reason": "no_identification_data",
        }

    # ---------------------------------------------------------
    # 5. Caso de seguridad
    # ---------------------------------------------------------
    return {
        "needed": True,
        "query_ready": False,
        "reason": "manual_review_required",
    }

def identify_resolved_song(
    metadata: dict,
    filename: str,
    client=None,
    limit: int = 5,
):
    """
    Resuelve la metadata local y decide si debe utilizarse
    MusicBrainz para verificar la identidad.

    IMPORTANTE:
    - No modifica SQLite.
    - No sobrescribe metadata original.
    - No persiste resultados externos.
    """

    resolved = resolve_metadata(
        metadata,
        filename,
    )

    title = resolved.get("title")
    artist = resolved.get("artist")

    decision = _should_verify_externally(
        resolved
    )

    result = {
        "title": title,
        "artist": artist,
        "album": metadata.get("album"),
        "year": metadata.get("year"),
        "duration": metadata.get("duration"),
        "confidence": resolved.get(
            "metadata_confidence",
            0.0,
        ),
        "source": "local",
        "status": resolved.get(
            "resolution_status",
            "unresolved",
        ),
        "external_ids": {},
        "resolution": resolved,
        "external_verification": {
            "needed": decision["needed"],
            "query_ready": decision["query_ready"],
            "reason": decision["reason"],
            "attempted": False,
        },
    }

    # No hay información suficiente para realizar
    # ninguna identificación externa.
    if not decision["query_ready"]:
        return result

    if not title or not artist:
        return result

    if client is None:
        client = create_musicbrainz_client()

    candidates = client.search_recordings(
        title=title,
        artist=artist,
        limit=limit,
    )

    result["external_verification"]["attempted"] = True

    if not candidates:
        result["external_verification"]["reason"] = (
            "no_musicbrainz_candidates"
        )

        result["source"] = "local"
        result["status"] = "unidentified_external"

        return result

    ranked_matches = rank_candidates(
    {
        **metadata,
        "normalized_title": title,
        "normalized_artist": artist,
    },
    candidates,
)

    best_match = ranked_matches[0]

    candidate = best_match["candidate"]

    score = best_match["score"]
    classification = best_match["classification"]

    result.update(
        {
            "title": candidate.get("title"),
            "artist": candidate.get("artist"),
            "duration": candidate.get(
                "duration"
            ),
            "confidence": score,
            "source": EXTERNAL_IDENTIFICATION_SOURCE,
            "status": classification,
            "external_ids": {
                "musicbrainz_recording": candidate.get(
                    "mbid"
                ),
            },
            "match": {
                "score": score,
                "classification": classification,
                "title_similarity": best_match[
                    "title_similarity"
                ],
                "artist_similarity": best_match[
                    "artist_similarity"
                ],
                "duration_similarity": best_match[
                    "duration_similarity"
                ],
            },
            "candidates_checked": len(
                ranked_matches
            ),
        }
    )

    return result


def identify_song_with_musicbrainz(
    metadata,
    client=None,
    limit=5,
):
    """
    Compatibilidad con la función anterior.

    Si se necesita identificación externa pero no se proporciona
    filename, se mantiene el comportamiento anterior basado
    directamente en la metadata disponible.
    """

    local_identification = identify_song(
        metadata
    )

    title = local_identification["title"]
    artist = local_identification["artist"]

    if not title:
        return {
            **local_identification,
            "source": EXTERNAL_IDENTIFICATION_SOURCE,
            "status": "unidentified",
            "confidence": 0.0,
            "external_ids": {},
        }

    if client is None:
        client = create_musicbrainz_client()

    candidates = client.search_recordings(
        title=title,
        artist=artist,
        limit=limit,
    )

    if not candidates:
        return {
            **local_identification,
            "source": EXTERNAL_IDENTIFICATION_SOURCE,
            "status": "unidentified",
            "confidence": 0.0,
            "external_ids": {},
        }

    ranked_matches = rank_candidates(
        metadata,
        candidates,
    )

    best_match = ranked_matches[0]

    candidate = best_match["candidate"]

    score = best_match["score"]
    classification = best_match["classification"]

    return {
        "title": candidate.get("title"),
        "artist": candidate.get("artist"),
        "album": local_identification.get("album"),
        "year": local_identification.get("year"),
        "duration": candidate.get("duration"),
        "confidence": score,
        "source": EXTERNAL_IDENTIFICATION_SOURCE,
        "status": classification,
        "external_ids": {
            "musicbrainz_recording": candidate.get(
                "mbid"
            ),
        },
        "match": {
            "score": score,
            "classification": classification,
            "title_similarity": best_match[
                "title_similarity"
            ],
            "artist_similarity": best_match[
                "artist_similarity"
            ],
            "duration_similarity": best_match[
                "duration_similarity"
            ],
        },
        "candidates_checked": len(
            ranked_matches
        ),
    }