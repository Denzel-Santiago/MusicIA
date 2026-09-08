from app.services.filename_parser import extract_artist_title_from_filename
def resolve_metadata(metadata: dict, filename: str):
    """
    Decide qué información utilizar para artista y título.

    Prioridad:

    1. Metadata real del archivo.
    2. Nombre del archivo cuando la metadata está incompleta.
    3. Dejar el campo vacío cuando no existe suficiente información.
    """

    original_artist = metadata.get("artist")
    original_title = metadata.get("title")
    title_source = metadata.get("title_source", "metadata")

    filename_result = extract_artist_title_from_filename(filename)

    filename_artist = filename_result.get("artist")
    filename_title = filename_result.get("title")
    filename_confidence = filename_result.get("confidence", 0.0)

    # -----------------------------------------
    # ARTISTA
    # -----------------------------------------

    if original_artist:
        normalized_artist = original_artist
        artist_source = "metadata"
        artist_confidence = 1.0

    elif filename_artist and filename_confidence >= 0.8:
        normalized_artist = filename_artist
        artist_source = "filename"
        artist_confidence = filename_confidence

    else:
        normalized_artist = None
        artist_source = None
        artist_confidence = 0.0

    # -----------------------------------------
    # TÍTULO
    # -----------------------------------------

    if original_title and title_source == "metadata":
        normalized_title = original_title
        title_source_result = "metadata"
        title_confidence = 1.0

    elif filename_title and filename_confidence >= 0.8:
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

    # -----------------------------------------
    # FUENTE GENERAL
    # -----------------------------------------

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
        metadata_source = next(iter(sources))

    else:
        metadata_source = None

    # -----------------------------------------
    # CONFIANZA
    # -----------------------------------------

    confidences = [
        artist_confidence,
        title_confidence,
    ]

    confidences = [
        confidence
        for confidence in confidences
        if confidence > 0
    ]

    metadata_confidence = min(confidences) if confidences else 0.0

    return {
        "artist": normalized_artist,
        "title": normalized_title,
        "metadata_source": metadata_source,
        "metadata_confidence": metadata_confidence,
    }
    
if __name__ == "__main__":

    tests = [
        {
            "metadata": {
                "artist": "Avicii",
                "title": "Hey Brother",
                "title_source": "metadata"
            },
            "filename": "Hey Brother.mp3"
        },
        {
            "metadata": {
                "artist": None,
                "title": "Avicii - The Nights",
                "title_source": "filename_fallback"
            },
            "filename": "Avicii - The Nights.mp3"
        },
        {
            "metadata": {
                "artist": None,
                "title": "Broken Arrows",
                "title_source": "filename_fallback"
            },
            "filename": "Broken Arrows.mp3"
        }
    ]

    for test in tests:

        result = resolve_metadata(
            test["metadata"],
            test["filename"]
        )

        print("\n-----------------------------")
        print(f"Archivo: {test['filename']}")
        print(f"Resultado: {result}")
