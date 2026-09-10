from __future__ import annotations

from app.services.filename_parser import (
    extract_artist_title_from_filename,
)
from app.services.metadata_quality import (
    evaluate_metadata_quality,
)


def _clean_filename_title_with_artist(
    original_title: str | None,
    filename_artist: str | None,
    filename_title: str | None,
) -> str | None:
    """
    Evita conservar un prefijo redundante del artista
    cuando el título proviene del fallback del filename.

    Ejemplo:

        original:
            "Avicii - The Nights"

        filename:
            artist = "Avicii"
            title = "The Nights"

        resultado:
            "The Nights"
    """

    if not original_title:
        return None

    if not filename_artist or not filename_title:
        return original_title

    original_clean = original_title.strip()
    artist_clean = filename_artist.strip()
    title_clean = filename_title.strip()

    prefix = f"{artist_clean} - "

    if original_clean.casefold().startswith(
        prefix.casefold()
    ):
        remaining_title = original_clean[
            len(prefix):
        ].strip()

        if remaining_title.casefold() == title_clean.casefold():
            return title_clean

    return original_title


def resolve_metadata(
    metadata: dict,
    filename: str,
):
    """
    Resuelve metadata local utilizando:

        1. Metadata original
        2. Nombre del archivo
        3. Evaluación de calidad

    IMPORTANTE:

    - NO modifica la metadata original.
    - NO modifica la base de datos.
    - NO consulta servicios externos.
    - La capa de calidad solamente aporta contexto.
    """

    # =========================================================
    # 1. Evaluar calidad de la metadata original
    # =========================================================

    quality = evaluate_metadata_quality(
        metadata,
        filename,
    )

    # =========================================================
    # 2. Obtener metadata original
    # =========================================================

    original_artist = metadata.get("artist")
    original_title = metadata.get("title")
    title_source = metadata.get(
        "title_source",
        "metadata",
    )

    # =========================================================
    # 3. Analizar filename
    # =========================================================

    filename_result = extract_artist_title_from_filename(
        filename
    )

    filename_artist = filename_result.get(
        "artist"
    )

    filename_title = filename_result.get(
        "title"
    )

    filename_confidence = filename_result.get(
        "confidence",
        0.0,
    )

    # =========================================================
    # 4. Resolver artista
    # =========================================================

    if original_artist:
        normalized_artist = original_artist

        artist_source = "metadata"

        artist_confidence = 1.0

    elif (
        filename_artist
        and filename_confidence >= 0.8
    ):
        normalized_artist = filename_artist

        artist_source = "filename"

        artist_confidence = filename_confidence

    else:
        normalized_artist = None

        artist_source = None

        artist_confidence = 0.0

    # =========================================================
    # 5. Resolver título
    # =========================================================

    if (
        original_title
        and title_source == "metadata"
    ):
        normalized_title = original_title

        title_source_result = "metadata"

        title_confidence = 1.0

    elif (
        original_title
        and title_source == "filename_fallback"
        and filename_artist
        and filename_title
        and filename_confidence >= 0.8
    ):
        normalized_title = (
            _clean_filename_title_with_artist(
                original_title,
                filename_artist,
                filename_title,
            )
        )

        title_source_result = "filename"

        title_confidence = filename_confidence

    elif (
        filename_title
        and filename_confidence >= 0.8
    ):
        normalized_title = filename_title

        title_source_result = "filename"

        title_confidence = filename_confidence

    elif original_title:
        normalized_title = original_title

        title_source_result = "filename"

        title_confidence = 0.4

    else:
        normalized_title = None

        title_source_result = None

        title_confidence = 0.0

    # =========================================================
    # 6. Determinar fuente combinada
    # =========================================================

    sources = {
        artist_source,
        title_source_result,
    }

    sources.discard(None)

    if sources == {"metadata"}:
        metadata_source = "metadata"

    elif sources == {"filename"}:
        metadata_source = "filename"

    elif len(sources) > 1:
        metadata_source = "mixed"

    elif sources == {"filename_fallback"}:
        metadata_source = "filename"

    elif sources:
        metadata_source = next(
            iter(sources)
        )

    else:
        metadata_source = None

     # =========================================================
    # 7. Calcular confianza de resolución local
    # =========================================================

    if (
        normalized_title
        and normalized_artist
    ):
        # Tenemos título + artista.
        #
        # La confianza representa la calidad de las fuentes
        # utilizadas para obtener ambos campos.

        metadata_confidence = min(
            artist_confidence,
            title_confidence,
        )

    elif normalized_title:
        # Solo tenemos título.
        #
        # Aunque el título provenga directamente de metadata,
        # la identificación todavía está incompleta porque
        # falta el artista.

        metadata_confidence = min(
            title_confidence,
            0.5,
        )

    elif normalized_artist:
        # Solo tenemos artista.
        #
        # También es una identificación incompleta.

        metadata_confidence = min(
            artist_confidence,
            0.5,
        )

    else:
        metadata_confidence = 0.0

    # =========================================================
    # 8. Estado de resolución local
    # =========================================================

    if (
        normalized_title
        and normalized_artist
    ):
        resolution_status = "resolved"

    elif (
        normalized_title
        or normalized_artist
    ):
        resolution_status = "partial"

    else:
        resolution_status = "unresolved"

    # =========================================================
    # 9. Resultado final
    # =========================================================

    return {
        # -----------------------------------------------
        # Metadata resuelta
        # -----------------------------------------------

        "title": normalized_title,

        "artist": normalized_artist,

        "metadata_source": metadata_source,

        "metadata_confidence": metadata_confidence,

        # -----------------------------------------------
        # Estado de resolución
        # -----------------------------------------------

        "resolution_status": resolution_status,

        # -----------------------------------------------
        # Calidad de metadata
        # -----------------------------------------------

        "quality": quality,

        # -----------------------------------------------
        # Información del filename
        # -----------------------------------------------

        "filename": {
            "artist": filename_artist,
            "title": filename_title,
            "confidence": filename_confidence,
        },

        # -----------------------------------------------
        # Metadata original
        # -----------------------------------------------

        "original": {
            "title": original_title,
            "artist": original_artist,
        },
    }


# =============================================================
# Pruebas manuales
# =============================================================

if __name__ == "__main__":

    tests = [
        {
            "filename": "Avicii - The Nights.mp3",
            "metadata": {
                "title": "The Nights",
                "artist": "Avicii",
                "title_source": "metadata",
            },
        },
        {
            "filename": "Avicii - Waiting For Love.mp3",
            "metadata": {
                "title": "Waiting For Love",
                "artist": None,
                "title_source": "filename_fallback",
            },
        },
        {
            "filename": "Broken Arrows.mp3",
            "metadata": {
                "title": "Broken Arrows",
                "artist": None,
                "title_source": "metadata",
            },
        },
        {
            "filename": (
                "(Letra) Hablame De Ti - "
                "Banda MS (Completa).mp3"
            ),
            "metadata": {
                "title": "Banda MS (Completa)",
                "artist": "(Letra) Hablame De Ti",
                "title_source": "metadata",
            },
        },
    ]

    for test in tests:

        result = resolve_metadata(
            test["metadata"],
            test["filename"],
        )

        print("\n=============================")

        print(
            f"Archivo: {test['filename']}"
        )

        print(
            f"Título resuelto: "
            f"{result['title']}"
        )

        print(
            f"Artista resuelto: "
            f"{result['artist']}"
        )

        print(
            f"Fuente: "
            f"{result['metadata_source']}"
        )

        print(
            f"Confianza: "
            f"{result['metadata_confidence']}"
        )

        print(
            f"Estado resolución: "
            f"{result['resolution_status']}"
        )

        quality = result["quality"]

        print(
            f"Calidad: "
            f"{quality['status']}"
        )

        print(
            f"Confianza calidad: "
            f"{quality['confidence']}"
        )

        print(
            f"Ruido contenido: "
            f"{quality['content_noise']}"
        )

        print("Razones:")

        for reason in quality["reasons"]:
            print(f"  - {reason}")