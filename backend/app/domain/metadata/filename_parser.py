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


PURE_VERSION_LABELS = (
    "original mix",
    "radio edit",
    "club mix",
    "extended mix",
    "extended version",
    "acoustic version",
    "live version",
    "live",
    "remix",
    "edit",
    "instrumental",
    "acoustic",
    "version",
)


def clean_extracted_text(value):
    if not value:
        return None

    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" -–—_")

    return value if value else None


def looks_like_versioned_title(value):
    if not value:
        return False

    normalized = value.lower()

    return any(
        re.search(pattern, normalized)
        for pattern in VERSION_PATTERNS
    )


def is_pure_version_label(value):
    """
    Determina si el texto corresponde únicamente a una etiqueta
    de versión musical.

    Ejemplos:
        Original Mix
        Radio Edit
        Club Mix
        Acoustic Version
        Remix

    Esto permite distinguir:

        Levels - Original Mix

    de:

        Avicii - For A Better Day (KSHMR Remix)
    """

    if not value:
        return False

    normalized = value.strip().lower()

    # Eliminar paréntesis exteriores.
    normalized = re.sub(
        r"^\((.*)\)$",
        r"\1",
        normalized,
    ).strip()

    return normalized in PURE_VERSION_LABELS


def extract_reversed_lyric_filename(name: str):
    """
    Detecta nombres de archivo donde el formato parece estar invertido:

        (Letra) Titulo - Artista (Completa)

    y devuelve:

        artist = Artista
        title  = Titulo

    La regla es deliberadamente conservadora para no invertir
    nombres de archivo normales como:

        Avicii - The Nights
    """

    if not name:
        return None

    match = re.match(
        r"^\((?:letra|lyrics?|lyric)\)\s*(.+?)\s*[-–—_]\s*(.+?)\s*\((?:completa|complete)\)$",
        name,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    title = clean_extracted_text(match.group(1))
    artist = clean_extracted_text(match.group(2))

    if not title or not artist:
        return None

    return {
        "artist": artist,
        "title": title,
        "confidence": 0.90,
    }




def extract_artist_title_from_filename(filename: str):
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
        
    
    reversed_result = extract_reversed_lyric_filename(name)

    if reversed_result:
        return reversed_result



    match = re.match(
        r"^(.+?)\s*[-–—_]\s*(.+)$",
        name,
    )

    if match:
        left = clean_extracted_text(match.group(1))
        right = clean_extracted_text(match.group(2))

        if left and right:

            # Si todo lo que está después del separador es
            # únicamente una etiqueta de versión, no asumimos
            # que la parte izquierda sea necesariamente el artista.
            #
            # Ejemplo:
            # Levels - Original Mix
            #
            # Se conserva como título completo.
            if is_pure_version_label(right):
                return {
                    "artist": None,
                    "title": name,
                    "confidence": 0.40,
                }

            # Si el lado derecho contiene información musical
            # real además de la versión, podemos interpretar
            # el lado izquierdo como artista.
            #
            # Ejemplo:
            # Avicii - For A Better Day (KSHMR Remix)
            #
            # Resultado:
            # artist = Avicii
            # title  = For A Better Day (KSHMR Remix)
            return {
                "artist": left,
                "title": right,
                "confidence": 0.90,
            }

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

        # Casos protegidos
        "Levels - Original Mix.mp3",
        "The Nights - Radio Edit.mp3",
        "Wake Me Up - Acoustic Version.mp3",
        "Some Song - Club Mix.mp3",

        # Casos que ahora deben separar correctamente
        "Avicii - For A Better Day (KSHMR Remix).mp3",
        "Avicii - Without You (AFISHAL Remix).mp3",
        "Avicii - All You Need Is Love (Original Mix) HQ.mp3",
        "Avicii - Some Song (Radio Edit).mp3",
        "Avicii - Song Title (Acoustic Version).mp3",

        # Otros casos
        "Avicii - Lonely Together.mp3",
        "Song Title feat. Artist.mp3",
        "Song Title (Live Version).mp3",
    ]

    for filename in tests:
        result = extract_artist_title_from_filename(filename)

        print("\n-----------------------------")
        print(f"Archivo: {filename}")
        print(f"Resultado: {result}")