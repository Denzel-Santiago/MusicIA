"""Identificación de canciones usando metadata local y fuentes externas."""

from __future__ import annotations

import re

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

    Esta función NO realiza consultas externas.
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
        "identity_status": "unverified",
        "external_ids": {},
    }


def _clean_external_query_text(value):
    """
    Limpia únicamente el texto utilizado para una consulta externa.

    Esta función NO modifica la metadata original.
    """

    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    # ---------------------------------------------------------
    # 1. Eliminar extensiones conocidas
    # ---------------------------------------------------------

    value = re.sub(
        r"\.(mp3|flac|wav|m4a|ogg)$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # 2. Normalizar espacios
    # ---------------------------------------------------------

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    # ---------------------------------------------------------
    # 3. Eliminar indicadores de contenido adicional
    # ---------------------------------------------------------

    value = re.sub(
        r"\((?:lyric video|lyrics video|music video|official video)\)",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\b(?:subtitulado|subtitulada|subtitles)\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s*[-–—]\s*youtube\s*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Casos como:
    # "Cant Catch Me Lyric"
    # "Cant Catch Me Lyrics"
    value = re.sub(
        r"\s+\b(?:lyric|lyrics)\b\s*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # 4. Limpiar separadores sobrantes
    # ---------------------------------------------------------

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip(" -–—_")

    return value if value else None


def _build_external_query_candidates(
    resolved_metadata,
    filename,
):
    """
    Construye y prioriza posibles pares artista/título
    para una búsqueda externa.

    La prioridad depende de la calidad de la información local:

    - Metadata normal:
        1. filename confiable
        2. resolución local
        3. candidato invertido

    - Metadata sospechosa:
        1. candidato invertido limpio
        2. filename confiable
        3. resolución local contaminada

    Esta función solo prepara consultas.
    No realiza consultas externas y no modifica datos persistentes.
    """

    candidates = []

    local_title = resolved_metadata.get("title")
    local_artist = resolved_metadata.get("artist")

    filename_data = resolved_metadata.get("filename", {})
    filename_title = filename_data.get("title")
    filename_artist = filename_data.get("artist")
    filename_confidence = filename_data.get("confidence", 0.0)

    quality = resolved_metadata.get("quality", {})
    quality_status = quality.get("status")

    def add_candidate(title, artist, reason):
        title = _clean_external_query_text(title)
        artist = _clean_external_query_text(artist)

        if not title:
            return

        candidate = {
            "title": title,
            "artist": artist,
            "reason": reason,
        }

        for existing in candidates:
            same_title = (
                existing["title"].casefold()
                == title.casefold()
            )

            same_artist = (
                (existing["artist"] or "").casefold()
                == (artist or "").casefold()
            )

            if same_title and same_artist:
                return

        candidates.append(candidate)

    # ---------------------------------------------------------
    # 1. Filename confiable
    # ---------------------------------------------------------
    #
    # Ejemplo:
    #
    # Avicii - The Nights.mp3
    #
    # -> The Nights / Avicii
    #
    if (
        filename_title
        and filename_artist
        and filename_confidence >= 0.8
    ):
        add_candidate(
            filename_title,
            filename_artist,
            "filename_resolution",
        )

    # ---------------------------------------------------------
    # 2. Resolución local
    # ---------------------------------------------------------
    #
    # Se conserva como alternativa.
    #
    if local_title and local_artist:
        add_candidate(
            local_title,
            local_artist,
            "local_resolution",
        )

    # ---------------------------------------------------------
    # 3. Filename posiblemente invertido
    # ---------------------------------------------------------
    #
    # Ejemplo:
    #
    # (Letra) Hablame De Ti - Banda MS (Completa).mp3
    #
    # El parser puede interpretar inicialmente:
    #
    # artista = (Letra) Hablame De Ti
    # título  = Banda MS (Completa)
    #
    # Pero también podemos probar la interpretación inversa:
    #
    # título  = Hablame De Ti
    # artista = Banda MS
    #
    if filename_artist and filename_title:

        possible_artist = re.sub(
            r"^\((?:letra|lyrics?)\)\s*",
            "",
            filename_title,
            flags=re.IGNORECASE,
        )

        possible_artist = re.sub(
            r"\s*\((?:completa|complete)\)\s*$",
            "",
            possible_artist,
            flags=re.IGNORECASE,
        )

        possible_title = re.sub(
            r"^\((?:letra|lyrics?)\)\s*",
            "",
            filename_artist,
            flags=re.IGNORECASE,
        )

        possible_title = _clean_external_query_text(
            possible_title
        )

        possible_artist = _clean_external_query_text(
            possible_artist
        )

        if possible_title and possible_artist:
            add_candidate(
                possible_title,
                possible_artist,
                "filename_reversed_candidate",
            )

    # ---------------------------------------------------------
    # 4. Recuperación mediante artista original
    # ---------------------------------------------------------
    #
    # Se utiliza únicamente cuando no tenemos artista local.
    #
    if not local_artist and filename:

        cleaned_filename = _clean_external_query_text(
            filename
        )

        if cleaned_filename:

            original_artist = resolved_metadata.get(
                "original",
                {},
            ).get("artist")

            if original_artist:

                remaining = re.sub(
                    re.escape(str(original_artist)),
                    "",
                    cleaned_filename,
                    count=1,
                    flags=re.IGNORECASE,
                ).strip(" -–—_")

                remaining = re.sub(
                    r"\b(?:new song|new track)\b",
                    "",
                    remaining,
                    flags=re.IGNORECASE,
                )

                remaining = re.sub(
                    r"\b\d{4}\b",
                    "",
                    remaining,
                )

                remaining = re.sub(
                    r"\s+",
                    " ",
                    remaining,
                ).strip()

                if remaining:
                    add_candidate(
                        remaining,
                        original_artist,
                        "original_artist_filename_recovery",
                    )

    # ---------------------------------------------------------
    # 5. Priorizar candidatos
    # ---------------------------------------------------------
    #
    # Aquí está la mejora principal.
    #
    # Cuando la metadata es sospechosa, damos prioridad a una
    # interpretación alternativa que elimine señales claras
    # de contaminación.
    #
    # En metadata normal, mantenemos filename confiable primero.
    #

    def candidate_priority(candidate):
        reason = candidate["reason"]

        if quality_status == "suspicious":

            if reason == "filename_reversed_candidate":
                return 0

            if reason == "filename_resolution":
                return 1

            if reason == "original_artist_filename_recovery":
                return 2

            if reason == "local_resolution":
                return 3

            return 4

        # Metadata normal

        if reason == "filename_resolution":
            return 0

        if reason == "local_resolution":
            return 1

        if reason == "original_artist_filename_recovery":
            return 2

        if reason == "filename_reversed_candidate":
            return 3

        return 4

    candidates.sort(
        key=candidate_priority
    )

    return candidates


def _should_verify_externally(resolved_metadata):
    """
    Determina si MusicAI debe intentar verificar la identidad
    mediante una fuente externa.
    """

    quality = resolved_metadata.get("quality", {})

    quality_status = quality.get("status")

    resolution_status = resolved_metadata.get(
        "resolution_status"
    )

    title = resolved_metadata.get("title")
    artist = resolved_metadata.get("artist")

    # ---------------------------------------------------------
    # 1. Metadata sospechosa
    # ---------------------------------------------------------

    if quality_status == "suspicious":
        return {
            "needed": True,
            "query_ready": True,
            "reason": "suspicious_metadata_requires_external_recovery",
        }

    # ---------------------------------------------------------
    # 2. Resolución completa
    #
    # Tener metadata completa NO significa identidad confirmada.
    # Por eso también verificamos estos casos.
    # ---------------------------------------------------------

    if (
        resolution_status == "resolved"
        and title
        and artist
    ):
        return {
            "needed": True,
            "query_ready": True,
            "reason": "local_resolution_requires_identity_verification",
        }

    # ---------------------------------------------------------
    # 3. Resolución incompleta
    # ---------------------------------------------------------

    if resolution_status != "resolved":

        if title and artist:
            return {
                "needed": True,
                "query_ready": True,
                "reason": "incomplete_resolution_with_artist_title",
            }

        if title or artist:
            return {
                "needed": True,
                "query_ready": True,
                "reason": "insufficient_local_data_external_recovery",
            }

        return {
            "needed": True,
            "query_ready": False,
            "reason": "no_identification_data",
        }

    return {
        "needed": True,
        "query_ready": False,
        "reason": "manual_review_required",
    }


def _identity_status_from_match(classification):
    """
    Convierte la clasificación del matcher en un estado
    explícito de identidad.
    """

    mapping = {
        "confirmed": "confirmed",
        "probable": "probable",
        "review": "review",
        "rejected": "rejected",
    }

    return mapping.get(
        classification,
        "review",
    )


def identify_resolved_song(
    metadata: dict,
    filename: str,
    client=None,
    limit: int = 5,
):
    """
    Resuelve metadata local y verifica identidad mediante MusicBrainz.

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
        "source": IDENTIFICATION_SOURCE,
        "status": resolved.get(
            "resolution_status",
            "unresolved",
        ),
        "identity_status": "unverified",
        "external_ids": {},
        "resolution": resolved,
        "external_verification": {
            "needed": decision["needed"],
            "query_ready": decision["query_ready"],
            "reason": decision["reason"],
            "attempted": False,
            "queries": [],
            "errors": [],
        },
    }

    query_candidates = _build_external_query_candidates(
        resolved,
        filename,
    )

    result["external_verification"]["queries"] = (
        query_candidates
    )

    if not decision["query_ready"]:
        if not title and not artist:
            result["identity_status"] = "fingerprint_required"

        return result

    if not query_candidates:
        result["external_verification"]["reason"] = (
            "no_external_query_candidates"
        )

        if resolved.get("resolution_status") == "resolved":
            result["identity_status"] = "unverified"
        else:
            result["identity_status"] = "fingerprint_required"

        return result

    if client is None:
        client = create_musicbrainz_client()

    all_ranked_matches = []

    for query_candidate in query_candidates:

        try:
            candidates = client.search_recordings(
                title=query_candidate["title"],
                artist=query_candidate["artist"],
                limit=limit,
            )

        except Exception as exc:
            error_message = (
                f"{type(exc).__name__}: {exc}"
            )

            result["external_verification"]["errors"].append(
                {
                    "query_title": query_candidate["title"],
                    "query_artist": query_candidate["artist"],
                    "error": error_message,
                }
            )

            continue

        result["external_verification"]["attempted"] = True

        if not candidates:
            continue

        ranking_metadata = {
    **metadata,
    "title": query_candidate["title"],
    "artist": query_candidate["artist"],
}

        ranked_matches = rank_candidates(
            ranking_metadata,
            candidates,
        )

        for match in ranked_matches:
            match["query_reason"] = (
                query_candidate["reason"]
            )

            match["query_title"] = (
                query_candidate["title"]
            )

            match["query_artist"] = (
                query_candidate["artist"]
            )

        all_ranked_matches.extend(
            ranked_matches
        )

    # ---------------------------------------------------------
    # No hubo candidatos válidos
    # ---------------------------------------------------------

    if not all_ranked_matches:

        if result["external_verification"]["errors"]:
            result["external_verification"]["reason"] = (
                "external_service_unavailable"
            )
        else:
            result["external_verification"]["reason"] = (
                "no_musicbrainz_candidates"
            )

        result["source"] = IDENTIFICATION_SOURCE

        if (
            resolved.get("resolution_status") == "resolved"
            and resolved.get("quality", {}).get("status")
            != "suspicious"
        ):
            result["identity_status"] = "unverified"
        else:
            result["identity_status"] = "fingerprint_required"

        return result

    # ---------------------------------------------------------
    # Mejor candidato
    # ---------------------------------------------------------

    all_ranked_matches.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    best_match = all_ranked_matches[0]

    candidate = best_match["candidate"]
    score = best_match["score"]
    classification = best_match["classification"]

    identity_status = _identity_status_from_match(
        classification
    )

    # ---------------------------------------------------------
    # IMPORTANTE:
    #
    # Un candidato REJECTED no puede reemplazar
    # nuestra identificación local.
    # ---------------------------------------------------------

    if classification == "rejected":

        result["external_verification"]["reason"] = (
            "best_musicbrainz_match_rejected"
        )

        result["identity_status"] = "unverified"

        result["match"] = {
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

            "query_reason": best_match.get(
                "query_reason"
            ),

            "query_title": best_match.get(
                "query_title"
            ),

            "query_artist": best_match.get(
                "query_artist"
            ),
        }

        result["candidates_checked"] = len(
            all_ranked_matches
        )

        # Conservamos título/artista locales.
        return result

    # ---------------------------------------------------------
    # Candidato suficientemente bueno
    # ---------------------------------------------------------

    result.update(
        {
            "title": candidate.get("title"),
            "artist": candidate.get("artist"),
            "duration": candidate.get("duration"),
            "confidence": score,
            "source": EXTERNAL_IDENTIFICATION_SOURCE,
            "status": classification,
            "identity_status": identity_status,
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

                "query_reason": best_match.get(
                    "query_reason"
                ),

                "query_title": best_match.get(
                    "query_title"
                ),

                "query_artist": best_match.get(
                    "query_artist"
                ),
            },
            "candidates_checked": len(
                all_ranked_matches
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

    Realiza identificación externa directamente desde metadata.
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
            "identity_status": "fingerprint_required",
            "confidence": 0.0,
            "external_ids": {},
        }

    if client is None:
        client = create_musicbrainz_client()

    try:
        candidates = client.search_recordings(
            title=title,
            artist=artist,
            limit=limit,
        )
    except Exception:
        return {
            **local_identification,
            "source": IDENTIFICATION_SOURCE,
            "identity_status": "unverified",
            "external_ids": {},
        }

    if not candidates:
        return {
            **local_identification,
            "source": IDENTIFICATION_SOURCE,
            "status": "unidentified",
            "identity_status": "unverified",
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

    if classification == "rejected":
        return {
            **local_identification,
            "source": IDENTIFICATION_SOURCE,
            "identity_status": "unverified",
            "external_ids": {},
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

    return {
        "title": candidate.get("title"),
        "artist": candidate.get("artist"),
        "album": local_identification.get("album"),
        "year": local_identification.get("year"),
        "duration": candidate.get("duration"),
        "confidence": score,
        "source": EXTERNAL_IDENTIFICATION_SOURCE,
        "status": classification,
        "identity_status": _identity_status_from_match(
            classification
        ),
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