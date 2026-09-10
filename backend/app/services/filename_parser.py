import re


VERSION_PATTERNS = (
    r"\boriginal mix\b",
    r"\bradio edit\b",
    r"\bclub mix\b",
    r"\bextended mix\b",
    r"\bextended version\b",
    r"\bacoustic version\b",
    r"\blive version\b",
    r"\blive\b",
    r"\bremix\b",
    r"\bedit\b",
    r"\binstrumental\b",
    r"\bacoustic\b",
    r"\bversion\b",
)


def clean_extracted_text(value):
    if not value:
        return None

    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" -–—_")

    return value if value else None


def looks_like_versioned_title(value):
    """
    Determina si un texto parece ser un título musical
    acompañado de información de versión.

    Ejemplos:

        Levels - Original Mix
        The Nights - Radio Edit
        Wake Me Up - Acoustic Version
        Some Song - Club Mix
    """

    if not value:
        return False

    normalized = value.lower()

    return any(
        re.search(pattern, normalized)
        for pattern in VERSION_PATTERNS
    )


def extract_artist_title_from_filename(filename: str):
    """
    Intenta obtener artista y título a partir del nombre del archivo.

    Ejemplos:

        Avicii - The Nights.mp3
            -> Avicii / The Nights

        Levels - Original Mix.mp3
            -> None / Levels - Original Mix
    """

    if not filename:
        return {
            "artist": None,
            "title": None,
            "confidence": 0.0,
        }

    name = re.sub(
        r"\.(mp3|flac|wav|m4a|ogg)$",
        "",
        filename,
        flags=re.IGNORECASE,
    )

    name = clean_extracted_text(name)

    if not name:
        return {
            "artist": None,
            "title": None,
            "confidence": 0.0,
        }

    # ---------------------------------------------------------
    # Detectar títulos que contienen información de versión
    # ---------------------------------------------------------

    if looks_like_versioned_title(name):
        return {
            "artist": None,
            "title": name,
            "confidence": 0.40,
        }

    # ---------------------------------------------------------
    # Intentar separar artista y título
    # ---------------------------------------------------------

    match = re.match(
        r"^(.+?)\s*[-–—_]\s*(.+)$",
        name,
    )

    if match:
        artist = clean_extracted_text(
            match.group(1)
        )

        title = clean_extracted_text(
            match.group(2)
        )

        if artist and title:
            return {
                "artist": artist,
                "title": title,
                "confidence": 0.90,
            }

    # ---------------------------------------------------------
    # Solo título
    # ---------------------------------------------------------

    return {
        "artist": None,
        "title": name,
        "confidence": 0.40,
    }


if __name__ == "__main__":

    tests = [
        "Avicii - The Nights.mp3",
        "Avicii - Waiting For Love.mp3",
        "Broken Arrows.mp3",
        "Levels - Original Mix.mp3",
        "The Nights - Radio Edit.mp3",
        "Wake Me Up - Acoustic Version.mp3",
        "Some Song - Club Mix.mp3",
        "Song Title (Live Version).mp3",
        "Avicii - Lonely Together.mp3",
    ]

    for filename in tests:

        result = extract_artist_title_from_filename(
            filename
        )

        print(
            "\n-----------------------------"
        )

        print(
            f"Archivo: {filename}"
        )

        print(
            f"Resultado: {result}"
        )