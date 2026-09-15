from __future__ import annotations

import re
from typing import Any

from app.services.metadata_matcher import (
    calculate_text_similarity,
    normalize_artist_for_comparison,
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


def _artist_name_similarity(
    local_artist: str,
    acoustic_artist: str,
) -> float:
    """
    Compara dos nombres individuales de artista.

    Reconoce:

        "Banda MS"
        "Banda MS de Sergio Lizárraga"

    como la misma identidad.

    También evita considerar como coincidencia una sola palabra
    genérica compartida:

        "Banda MS"
        "Banda El Recodo"

    """

    local_normalized = local_artist.strip()
    acoustic_normalized = acoustic_artist.strip()

    if not local_normalized or not acoustic_normalized:
        return 0.0

    # Coincidencia exacta.
    if local_normalized == acoustic_normalized:
        return 1.0

    local_words = local_normalized.split()
    acoustic_words = acoustic_normalized.split()

    if not local_words or not acoustic_words:
        return 0.0

    # ---------------------------------------------------------
    # Coincidencia por prefijo.
    #
    # "banda ms"
    # "banda ms de sergio lizarraga"
    #
    # El nombre corto coincide completamente con el comienzo
    # del nombre largo.
    # ---------------------------------------------------------

    if len(local_words) >= 2 and len(local_words) < len(acoustic_words):
        if acoustic_words[:len(local_words)] == local_words:
            return 1.0

    if len(acoustic_words) >= 2 and len(acoustic_words) < len(local_words):
        if local_words[:len(acoustic_words)] == acoustic_words:
            return 1.0

    # ---------------------------------------------------------
    # Coincidencia exacta por conjunto de palabras.
    #
    # Solo permitimos esto cuando ambos nombres tienen al
    # menos dos palabras.
    #
    # Así evitamos:
    #
    # "Banda"
    # "Banda MS"
    #
    # como coincidencia válida.
    # ---------------------------------------------------------

    if len(local_words) >= 2 and len(acoustic_words) >= 2:
        local_word_set = set(local_words)
        acoustic_word_set = set(acoustic_words)

        if (
            local_word_set.issubset(acoustic_word_set)
            or acoustic_word_set.issubset(local_word_set)
        ):
            return 1.0

    # ---------------------------------------------------------
    # Si solamente hay una palabra en alguno de los nombres,
    # NO hacemos similitud textual parcial.
    #
    # Esto evita falsos positivos con palabras genéricas como:
    #
    # "Banda"
    # "Banda MS"
    # ---------------------------------------------------------

    if len(local_words) < 2 or len(acoustic_words) < 2:
        return 0.0

    # ---------------------------------------------------------
    # Último recurso: similitud textual.
    #
    # Aquí ya sabemos que ambos nombres contienen al menos
    # dos palabras.
    # ---------------------------------------------------------

    textual_similarity = calculate_text_similarity(
        local_normalized,
        acoustic_normalized,
    )

    # Una similitud textual baja no es suficiente para considerar
    # que dos artistas son compatibles.
    #
    # Esto evita falsos positivos como:
    #
    #   "Banda MS"
    #   "Banda El Recodo"
    #
    # donde únicamente coincide una palabra genérica.
    if textual_similarity >= 0.80:
        return textual_similarity

    return 0.0


def _artist_credit_similarity(
    local_artist: str | None,
    acoustic_artist: str | None,
) -> float:
    """
    Compara artistas teniendo en cuenta créditos múltiples y
    diferentes formas de acreditar al mismo artista.

    Casos soportados:

        Avicii
        Avicii, Billy Raffoul

    y:

        Avicii Feat. Sandro Cavazza
        Avicii, Sandro Cavazza

    También reconoce formas abreviadas:

        Banda MS
        Banda MS de Sergio Lizárraga
    """

    local_tokens = _artist_credit_tokens(local_artist)
    acoustic_tokens = _artist_credit_tokens(acoustic_artist)

    if not local_tokens or not acoustic_tokens:
        return 0.0

    # Coincidencia exacta de todos los créditos.
    if local_tokens == acoustic_tokens:
        return 1.0

    # ---------------------------------------------------------
    # CASO IMPORTANTE:
    #
    # Si todos los artistas locales aparecen correctamente
    # dentro de los artistas acústicos, consideramos que la
    # identidad local es compatible.
    #
    # Ejemplo:
    #
    # local:
    #   {"avicii"}
    #
    # acústico:
    #   {"avicii", "billy raffoul"}
    #
    # Esto debe ser 1.0.
    # ---------------------------------------------------------

    local_matches = []

    for local_token in local_tokens:
        best_match = 0.0

        for acoustic_token in acoustic_tokens:
            similarity = _artist_name_similarity(
                local_token,
                acoustic_token,
            )

            best_match = max(
                best_match,
                similarity,
            )

        local_matches.append(best_match)

    if local_matches and min(local_matches) >= 1.0:
        return 1.0

    # ---------------------------------------------------------
    # CASO INVERSO:
    #
    # Si todos los artistas acústicos aparecen dentro de los
    # artistas locales, también son compatibles.
    #
    # Ejemplo:
    #
    # local:
    #   Avicii Feat. Sandro Cavazza
    #
    # acústico:
    #   Avicii, Sandro Cavazza
    #
    # ---------------------------------------------------------

    acoustic_matches = []

    for acoustic_token in acoustic_tokens:
        best_match = 0.0

        for local_token in local_tokens:
            similarity = _artist_name_similarity(
                local_token,
                acoustic_token,
            )

            best_match = max(
                best_match,
                similarity,
            )

        acoustic_matches.append(best_match)

    if acoustic_matches and min(acoustic_matches) >= 1.0:
        return 1.0

    # ---------------------------------------------------------
    # Si no existe una coincidencia completa, calculamos una
    # similitud parcial.
    #
    # Importante:
    # no dejamos que una sola palabra genérica produzca una
    # coincidencia significativa.
    # ---------------------------------------------------------

    if not local_matches:
        return 0.0

    return round(
        sum(local_matches) / len(local_matches),
        4,
    )


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