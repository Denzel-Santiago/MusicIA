from __future__ import annotations

from app.services.filename_parser import (
    extract_artist_title_from_filename,
)

from app.services.metadata_quality import (
    evaluate_metadata_quality,
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _clean_filename_title_with_artist(
    original_title: str | None,
    filename_artist: str | None,
    filename_title: str | None,
) -> str | None:
    """
    Limpia un título proveniente de filename cuando el título
    original contiene también el nombre del artista.

    Ejemplo:

        original_title:
            Avicii - Waiting For Love

        filename:
            Avicii - Waiting For Love

        resultado:
            Waiting For Love
    """

    if not original_title:
        return filename_title

    if not filename_artist or not filename_title:
        return original_title

    original_title_normalized = (
        str(original_title).strip()
    )

    filename_artist_normalized = (
        str(filename_artist).strip()
    )

    # --------------------------------------------------------
    # Si el título comienza con "Artista - "
    # eliminamos esa parte.
    # --------------------------------------------------------

    prefixes = (
        f"{filename_artist_normalized} - ",
        f"{filename_artist_normalized} – ",
        f"{filename_artist_normalized} — ",
        f"{filename_artist_normalized}_",
    )

    for prefix in prefixes:
        if original_title_normalized.lower().startswith(
            prefix.lower()
        ):
            cleaned = (
                original_title_normalized[
                    len(prefix):
                ].strip()
            )

            if cleaned:
                return cleaned

    # --------------------------------------------------------
    # Si coincide exactamente con el filename_title,
    # usamos el título extraído.
    # --------------------------------------------------------

    if (
        original_title_normalized.lower()
        == filename_title.lower()
    ):
        return filename_title

    return original_title


# ============================================================
# NUEVA FUNCIÓN AUXILIAR
# ============================================================

def _metadata_title_is_filename_contaminated(
    original_title: str | None,
    original_artist: str | None,
    filename_artist: str | None,
    filename_title: str | None,
    filename_confidence: float,
) -> bool:
    """
    Determina si el título de metadata parece ser realmente
    una combinación de:

        Artista - Título

    que el filename ya logró separar correctamente.

    Ejemplo:

        original_title:
            Avicii - The Nights

        original_artist:
            None

        filename:
            Avicii - The Nights

        filename_artist:
            Avicii

        filename_title:
            The Nights

    En este caso la metadata del título se considera
    contaminada/incompleta y se prefiere la información
    estructurada del filename.
    """

    if not original_title:
        return False

    if original_artist:
        return False

    if not filename_artist or not filename_title:
        return False

    if filename_confidence < 0.8:
        return False

    original_normalized = (
        str(original_title).strip().lower()
    )

    filename_artist_normalized = (
        str(filename_artist).strip().lower()
    )

    filename_title_normalized = (
        str(filename_title).strip().lower()
    )

    # --------------------------------------------------------
    # Caso esperado:
    #
    # "Avicii - The Nights"
    #
    # debe corresponder a:
    #
    # artist = "Avicii"
    # title  = "The Nights"
    # --------------------------------------------------------

    expected_titles = (
        f"{filename_artist_normalized} - "
        f"{filename_title_normalized}",

        f"{filename_artist_normalized} – "
        f"{filename_title_normalized}",

        f"{filename_artist_normalized} — "
        f"{filename_title_normalized}",

        f"{filename_artist_normalized}_"
        f"{filename_title_normalized}",
    )

    return original_normalized in expected_titles


# ============================================================
# RESOLVER PRINCIPAL
# ============================================================

def resolve_metadata(
    metadata: dict,
    filename: str,
) -> dict:
    """
    Resuelve la identidad local de una canción.

    Prioridad general:

    1. Metadata confiable.
    2. Filename cuando la metadata está incompleta.
    3. Filename cuando la metadata es sospechosa.
    4. Filename cuando el título de metadata está contaminado
       con el patrón "Artista - Título".
    5. Conservación de metadata cuando no existe evidencia
       suficiente para reemplazarla.

    Este resolver NO modifica la base de datos.
    """

    metadata = metadata or {}

    # ========================================================
    # 1. Evaluar calidad de metadata
    # ========================================================

    quality = evaluate_metadata_quality(
        metadata,
        filename,
    )

    quality_status = quality.get(
        "status",
        "unknown",
    )

    # ========================================================
    # 2. Obtener metadata original
    # ========================================================

    original_artist = metadata.get(
        "artist"
    )

    original_title = metadata.get(
        "title"
    )

    title_source = metadata.get(
        "title_source",
        "metadata",
    )

    # ========================================================
    # 3. Analizar filename
    # ========================================================

    filename_result = (
        extract_artist_title_from_filename(
            filename
        )
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

    # ========================================================
    # 4. Detectar metadata de título contaminada
    # ========================================================

    contaminated_title = (
        _metadata_title_is_filename_contaminated(
            original_title=original_title,
            original_artist=original_artist,
            filename_artist=filename_artist,
            filename_title=filename_title,
            filename_confidence=filename_confidence,
        )
    )

    # ========================================================
    # 5. Determinar si debemos preferir filename
    # ========================================================

    prefer_filename = (
        (
            quality_status == "suspicious"
            and filename_confidence >= 0.8
            and filename_artist
            and filename_title
        )
        or contaminated_title
        or (
            not original_artist
            and filename_confidence >= 0.8
            and filename_artist
            and filename_title
        )
    )

    # ========================================================
    # 6. Resolver artista
    # ========================================================

    if prefer_filename:

        normalized_artist = filename_artist

        artist_source = "filename"

        artist_confidence = (
            filename_confidence
        )

    elif original_artist:

        normalized_artist = original_artist

        artist_source = "metadata"

        artist_confidence = 1.0

    elif (
        filename_artist
        and filename_confidence >= 0.8
    ):

        normalized_artist = filename_artist

        artist_source = "filename"

        artist_confidence = (
            filename_confidence
        )

    else:

        normalized_artist = None

        artist_source = None

        artist_confidence = 0.0

    # ========================================================
    # 7. Resolver título
    # ========================================================

    if prefer_filename:

        normalized_title = filename_title

        title_source_result = "filename"

        title_confidence = (
            filename_confidence
        )

    elif (
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

        title_confidence = (
            filename_confidence
        )

    elif (
        filename_title
        and filename_confidence >= 0.8
    ):

        normalized_title = filename_title

        title_source_result = "filename"

        title_confidence = (
            filename_confidence
        )

    elif original_title:

        normalized_title = original_title

        title_source_result = "metadata"

        title_confidence = 0.4

    else:

        normalized_title = None

        title_source_result = None

        title_confidence = 0.0

    # ========================================================
    # 8. Determinar fuente combinada
    # ========================================================

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

    # ========================================================
    # 9. Calcular confianza de resolución
    # ========================================================

    if (
        normalized_title
        and normalized_artist
    ):

        metadata_confidence = min(
            artist_confidence,
            title_confidence,
        )

    elif normalized_title:

        metadata_confidence = min(
            title_confidence,
            0.5,
        )

    elif normalized_artist:

        metadata_confidence = min(
            artist_confidence,
            0.5,
        )

    else:

        metadata_confidence = 0.0

    # ========================================================
    # 10. Estado de resolución
    # ========================================================

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

    # ========================================================
    # 11. Resultado final
    # ========================================================

    return {

        # ----------------------------------------------------
        # Metadata resuelta
        # ----------------------------------------------------

        "title": normalized_title,

        "artist": normalized_artist,

        "metadata_source": metadata_source,

        "metadata_confidence": (
            metadata_confidence
        ),

        # ----------------------------------------------------
        # Estado
        # ----------------------------------------------------

        "resolution_status": (
            resolution_status
        ),

        # ----------------------------------------------------
        # Calidad
        # ----------------------------------------------------

        "quality": quality,

        # ----------------------------------------------------
        # Información del filename
        # ----------------------------------------------------

        "filename": {

            "artist": filename_artist,

            "title": filename_title,

            "confidence": filename_confidence,

        },

        # ----------------------------------------------------
        # Metadata original
        # ----------------------------------------------------

        "original": {

            "title": original_title,

            "artist": original_artist,

        },

    }