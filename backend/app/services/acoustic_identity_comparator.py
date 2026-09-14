from __future__ import annotations

import re
from typing import Any

from app.services.metadata_matcher import (
    calculate_text_similarity,
    normalize_artist_for_comparison,
    normalize_for_comparison,
)


class AcousticIdentityComparatorError(Exception):
    """Error al comparar metadata local con identidad acústica."""


def _artist_credit_tokens(value: str | None) -> set[str]:
    """
    Convierte los créditos de artistas en un conjunto de nombres
    comparables.

    Ejemplos:

        "Avicii"
        -> {"avicii"}

        "Avicii Feat. Sandro Cavazza"
        -> {"avicii", "sandro cavazza"}

        "Avicii, Sandro Cavazza"
        -> {"avicii", "sandro cavazza"}
    """

    if not value:
        return set()

    normalized = normalize_artist_for_comparison(value)

    if not normalized:
        return set()

    normalized = re.sub(
        r"\bfeat\b",
        "|",
        normalized,
    )

    normalized = re.sub(
        r"\band\b",
        "|",
        normalized,
    )

    normalized = re.sub(
        r"\s*\|\s*",
        "|",
        normalized,
    )

    parts = [
        part.strip()
        for part in normalized.split("|")
        if part.strip()
    ]

    return set(parts)


def _artist_credit_similarity(
    local_artist: str | None,
    acoustic_artist: str | None,
) -> float:
    """
    Compara artistas teniendo en cuenta créditos múltiples.

    La comparación permite reconocer casos como:

        Avicii
        Avicii, Billy Raffoul

    y:

        Avicii Feat. Sandro Cavazza
        Avicii, Sandro Cavazza
    """

    local_tokens = _artist_credit_tokens(local_artist)
    acoustic_tokens = _artist_credit_tokens(acoustic_artist)

    if not local_tokens or not acoustic_tokens:
        return 0.0

    if local_tokens == acoustic_tokens:
        return 1.0

    local_in_acoustic = local_tokens.issubset(
        acoustic_tokens
    )

    acoustic_in_local = acoustic_tokens.issubset(
        local_tokens
    )

    if local_in_acoustic or acoustic_in_local:
        return 1.0

    best_matches = []

    for local_token in local_tokens:
        token_best = 0.0

        for acoustic_token in acoustic_tokens:
            similarity = calculate_text_similarity(
                local_token,
                acoustic_token,
            )

            token_best = max(
                token_best,
                similarity,
            )

        best_matches.append(token_best)

    if not best_matches:
        return 0.0

    return sum(best_matches) / len(best_matches)


def _title_similarity(
    local_title: str | None,
    acoustic_title: str | None,
) -> float:
    """
    Compara títulos ignorando únicamente diferencias de formato
    que no deberían afectar la identidad textual.

    Por ahora conserva información de versiones/remixes.
    """

    return calculate_text_similarity(
        local_title,
        acoustic_title,
    )


def _classify_comparison(
    title_similarity: float,
    artist_similarity: float,
) -> str:
    """
    Clasifica la compatibilidad entre las dos identidades.
    """

    if (
        title_similarity >= 0.90
        and artist_similarity >= 0.90
    ):
        return "confirmed"

    if (
        title_similarity >= 0.70
        and artist_similarity >= 0.70
    ):
        return "probable"

    if (
        title_similarity < 0.50
        or artist_similarity < 0.50
    ):
        return "conflict"

    return "review"


def _build_decision(
    classification: str,
    acoustic_score: float | None,
    title_similarity: float,
    artist_similarity: float,
) -> tuple[str, str]:
    """
    Determina la acción recomendada sin modificar ninguna fuente.
    """

    if classification == "confirmed":
        return (
            "identity_confirmed",
            "La identidad local y la identidad acústica "
            "son compatibles tanto por título como por artista.",
        )

    if classification == "probable":
        if (
            acoustic_score is not None
            and acoustic_score >= 0.90
        ):
            return (
                "acoustic_identity_preferred",
                "La identidad acústica presenta una confianza "
                "alta y la identidad local es compatible.",
            )

        return (
            "review_recommended",
            "Existe una coincidencia probable, pero la "
            "confianza acústica no es suficiente para "
            "preferir automáticamente una fuente.",
        )

    if classification == "conflict":
        if (
            acoustic_score is not None
            and acoustic_score >= 0.90
            and title_similarity < 0.50
            and artist_similarity < 0.50
        ):
            return (
                "strong_acoustic_conflict",
                "El fingerprint presenta una coincidencia "
                "acústica alta, pero tanto el título como el "
                "artista son incompatibles. Se requiere "
                "investigación adicional antes de reemplazar "
                "la identidad local.",
            )

        if (
            acoustic_score is not None
            and acoustic_score >= 0.90
        ):
            return (
                "review_required",
                "Existe un conflicto entre las identidades, "
                "aunque la confianza acústica es alta. "
                "Se requiere revisión antes de modificar "
                "la metadata.",
            )

        return (
            "review_required",
            "La identidad local y la identidad acústica "
            "entran en conflicto y no existe suficiente "
            "evidencia para resolverlo automáticamente.",
        )

    if classification == "review":
        return (
            "review_recommended",
            "Existe una coincidencia parcial. "
            "Se recomienda revisión antes de modificar "
            "la metadata.",
        )

    return (
        "no_action",
        "No existe suficiente información para tomar "
        "una decisión automática.",
    )


def compare_acoustic_identity(
    local_metadata: dict[str, Any],
    acoustic_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Compara la identidad local de MusicAI contra la identidad
    obtenida mediante fingerprint acústico.

    Esta función NO modifica SQLite ni ninguna metadata.
    """

    if not local_metadata:
        raise AcousticIdentityComparatorError(
            "No se proporcionó metadata local."
        )

    if not acoustic_metadata:
        raise AcousticIdentityComparatorError(
            "No se proporcionó identidad acústica."
        )

    acoustic_status = acoustic_metadata.get(
        "status"
    )

    if acoustic_status != "identified":
        return {
            "status": "not_comparable",
            "classification": "no_acoustic_identity",
            "decision": "no_action",
            "reason": (
                "No existe una identidad acústica completa "
                "para comparar."
            ),
            "title_similarity": None,
            "artist_similarity": None,
            "overall_similarity": None,
            "acoustic_score": acoustic_metadata.get(
                "acoustid_score"
            ),
            "local": {
                "title": local_metadata.get("title"),
                "artist": local_metadata.get("artist"),
            },
            "acoustic": {
                "title": acoustic_metadata.get("title"),
                "artist": acoustic_metadata.get("artist"),
            },
        }

    local_title = local_metadata.get("title")
    local_artist = local_metadata.get("artist")

    acoustic_title = acoustic_metadata.get("title")
    acoustic_artist = acoustic_metadata.get("artist")

    title_similarity = _title_similarity(
        local_title,
        acoustic_title,
    )

    artist_similarity = _artist_credit_similarity(
        local_artist,
        acoustic_artist,
    )

    overall_similarity = (
        title_similarity + artist_similarity
    ) / 2

    acoustic_score = acoustic_metadata.get(
        "acoustid_score"
    )

    classification = _classify_comparison(
        title_similarity=title_similarity,
        artist_similarity=artist_similarity,
    )

    decision, reason = _build_decision(
        classification=classification,
        acoustic_score=acoustic_score,
        title_similarity=title_similarity,
        artist_similarity=artist_similarity,
    )

    return {
        "status": "compared",
        "classification": classification,
        "decision": decision,
        "reason": reason,
        "title_similarity": round(
            title_similarity,
            4,
        ),
        "artist_similarity": round(
            artist_similarity,
            4,
        ),
        "overall_similarity": round(
            overall_similarity,
            4,
        ),
        "acoustic_score": acoustic_score,
        "local": {
            "title": local_title,
            "artist": local_artist,
        },
        "acoustic": {
            "title": acoustic_title,
            "artist": acoustic_artist,
        },
    }