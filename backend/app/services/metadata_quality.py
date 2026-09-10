from __future__ import annotations

import re
from typing import Any

from app.services.filename_parser import (
    extract_artist_title_from_filename,
)


# Indicadores fuertes de que el nombre del archivo o la metadata
# contiene información adicional proveniente del contenido publicado.
CONTENT_NOISE_PATTERNS = (
    r"\blyric video\b",
    r"\blyrics video\b",
    r"\bletra\b",
    r"\bletras\b",
    r"\bsubtitulado\b",
    r"\bsubtitulada\b",
    r"\bsubtitles\b",
    r"\bmusic video\b",
    r"\bofficial video\b",
)


def _contains_content_noise(value: str | None) -> bool:
    """
    Detecta indicadores de contenido adicional.

    Ejemplos:
        "Cant Catch Me (Lyric Video)" -> True
        "Hablame De Ti (Subtitulada)" -> True
        "The Nights" -> False
    """
    if not value:
        return False

    normalized = str(value).lower()

    return any(
        re.search(pattern, normalized)
        for pattern in CONTENT_NOISE_PATTERNS
    )


def _same_text(
    value_a: str | None,
    value_b: str | None,
) -> bool:
    """
    Compara dos textos ignorando mayúsculas/minúsculas
    y espacios exteriores.
    """
    if not value_a or not value_b:
        return False

    return (
        value_a.strip().casefold()
        == value_b.strip().casefold()
    )


def evaluate_metadata_quality(
    metadata: dict[str, Any],
    filename: str,
) -> dict[str, Any]:
    """
    Evalúa la calidad aparente de la metadata local.

    IMPORTANTE:
    - NO modifica metadata.
    - NO modifica la base de datos.
    - NO consulta servicios externos.

    Estados:

        trusted:
            Tenemos suficiente información para considerar
            la metadata razonablemente confiable.

        unknown:
            La metadata está incompleta o necesitamos
            una fuente externa para confirmar la identidad.

        suspicious:
            Existe una señal fuerte de que algún campo
            está contaminado o es incorrecto.

    También devuelve:

        content_noise:
            Indica si se detectó ruido relacionado con
            contenido publicado, como letras o videos.

        reasons:
            Explica por qué se obtuvo el resultado.
    """

    original_title = metadata.get("title")
    original_artist = metadata.get("artist")

    filename_result = extract_artist_title_from_filename(
        filename
    )

    filename_artist = filename_result.get("artist")
    filename_title = filename_result.get("title")
    filename_confidence = filename_result.get(
        "confidence",
        0.0,
    )

    reasons: list[str] = []

    # =========================================================
    # 1. Detectar ruido de contenido
    # =========================================================

    title_has_noise = _contains_content_noise(
        original_title
    )

    artist_has_noise = _contains_content_noise(
        original_artist
    )

    filename_has_noise = _contains_content_noise(
        filename
    )

    content_noise = (
        title_has_noise
        or artist_has_noise
        or filename_has_noise
    )

    if title_has_noise:
        reasons.append(
            "El título contiene indicadores de contenido adicional."
        )

    if artist_has_noise:
        reasons.append(
            "El artista contiene indicadores de contenido adicional."
        )

    if filename_has_noise:
        reasons.append(
            "El nombre del archivo contiene indicadores de contenido adicional."
        )

    # =========================================================
    # 2. Comprobar existencia básica de metadata
    # =========================================================

    if not original_title and not original_artist:
        return {
            "status": "unknown",
            "confidence": 0.0,
            "content_noise": content_noise,
            "reasons": [
                "No existe título ni artista en la metadata."
            ],
        }

    if not original_artist:
        reasons.append(
            "La metadata no contiene artista."
        )

    if not original_title:
        reasons.append(
            "La metadata no contiene título."
        )

    # =========================================================
    # 3. Analizar información recuperable desde filename
    # =========================================================

    filename_agrees = False
    filename_conflict = False
    artist_recoverable = False

    if (
        filename_confidence >= 0.8
        and filename_artist
        and filename_title
    ):
        # -----------------------------------------------------
        # Artista
        # -----------------------------------------------------

        if original_artist:
            artist_matches = _same_text(
                original_artist,
                filename_artist,
            )

            if not artist_matches:
                reasons.append(
                    "El artista de la metadata no coincide "
                    "literalmente con el nombre del archivo."
                )

                # IMPORTANTE:
                #
                # Esto NO es suficiente para marcar suspicious.
                #
                # Puede tratarse de:
                #   Avicii vs Avicii & Nicky Romero
                #   Avicii feat. X vs Avicii
                #   Avicii vs Nicky Romero
                #   etc.
                #
                # La identificación real se hará después
                # mediante el resolver y MusicBrainz.

        else:
            artist_recoverable = True

            reasons.append(
                "El artista puede recuperarse de forma confiable "
                "desde el nombre del archivo."
            )

        # -----------------------------------------------------
        # Título
        # -----------------------------------------------------

        if original_title:
            title_matches = _same_text(
                original_title,
                filename_title,
            )

            if title_matches:
                filename_agrees = True
            else:
                reasons.append(
                    "El título de la metadata no coincide "
                    "literalmente con el nombre del archivo."
                )

        else:
            reasons.append(
                "El título puede recuperarse de forma confiable "
                "desde el nombre del archivo."
            )

    # =========================================================
    # 4. Determinar si realmente existe un conflicto fuerte
    # =========================================================

    #
    # La regla anterior era:
    #
    #     metadata != filename -> suspicious
    #
    # Eso era demasiado agresivo.
    #
    # Ahora:
    #
    # - Metadata incompleta -> unknown
    # - Diferencias entre metadata y filename -> unknown
    # - Ruido en título -> puede seguir siendo trusted
    # - Ruido en artista -> suspicious
    #
    # La validación definitiva de identidad la hará
    # posteriormente MusicBrainz / fingerprinting.
    #

    if artist_has_noise:
        return {
            "status": "suspicious",
            "confidence": 0.4,
            "content_noise": content_noise,
            "reasons": reasons,
        }

    # ---------------------------------------------------------
    # Metadata completa
    # ---------------------------------------------------------

    if original_title and original_artist:

        if filename_agrees:
            reasons.append(
                "Artista y título coinciden con el nombre del archivo."
            )

            return {
                "status": "trusted",
                "confidence": 0.9,
                "content_noise": content_noise,
                "reasons": reasons,
            }

               # Una diferencia entre metadata y filename no significa
        # necesariamente que la metadata sea incorrecta.
        #
        # El filename puede contener:
        #   - HQ
        #   - Official
        #   - Bonus Track
        #   - nombres alternativos
        #   - información de publicación
        #   - versiones o ediciones
        #
        # Si tenemos título + artista y no existe una señal fuerte
        # de contaminación, mantenemos la metadata como confiable.

        reasons.append(
            "La metadata está completa y no presenta una señal fuerte "
            "de contaminación."
        )

        return {
            "status": "trusted",
            "confidence": 0.8,
            "content_noise": content_noise,
            "reasons": reasons,
        }

    # ---------------------------------------------------------
    # Metadata incompleta
    # ---------------------------------------------------------

    if original_title and not original_artist:
        return {
            "status": "unknown",
            "confidence": 0.5,
            "content_noise": content_noise,
            "reasons": reasons,
        }

    if original_artist and not original_title:
        return {
            "status": "unknown",
            "confidence": 0.5,
            "content_noise": content_noise,
            "reasons": reasons,
        }

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------

    return {
        "status": "unknown",
        "confidence": 0.0,
        "content_noise": content_noise,
        "reasons": reasons,
    }


# =============================================================
# Pruebas unitarias manuales
# =============================================================

if __name__ == "__main__":

    tests = [
        {
            "filename": "Avicii - The Nights.mp3",
            "metadata": {
                "title": "The Nights",
                "artist": "Avicii",
            },
        },
        {
            "filename": "Avicii - Waiting For Love.mp3",
            "metadata": {
                "title": "Waiting For Love",
                "artist": None,
            },
        },
        {
            "filename": "Broken Arrows.mp3",
            "metadata": {
                "title": "Broken Arrows",
                "artist": None,
            },
        },
        {
            "filename": "(Letra) Hablame De Ti - Banda MS (Completa).mp3",
            "metadata": {
                "title": "Banda MS (Completa)",
                "artist": "(Letra) Hablame De Ti",
            },
        },
        {
            "filename": "Levels - Original Mix.mp3",
            "metadata": {
                "title": "Levels - Original Mix",
                "artist": None,
            },
        },
        {
            "filename": "Avicii - Cant Catch Me (Lyric Video).mp3",
            "metadata": {
                "title": "Cant Catch Me (Lyric Video)",
                "artist": "Avicii",
            },
        },
        {
            "filename": "Avicii - All You Need Is Love (Original Mix) HQ.mp3",
            "metadata": {
                "title": "All You Need Is Love (Original Mix) HQ",
                "artist": "Avicii",
            },
        },
    ]

    for test in tests:

        result = evaluate_metadata_quality(
            test["metadata"],
            test["filename"],
        )

        print("\n=============================")
        print(f"Archivo: {test['filename']}")
        print(f"Resultado: {result}")