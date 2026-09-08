import re


def clean_extracted_text(value):
    if not value:
        return None

    value = value.strip()

    # Eliminar espacios múltiples
    value = re.sub(r"\s+", " ", value)

    # Eliminar separadores sobrantes
    value = value.strip(" -–—_")

    return value if value else None


def extract_artist_title_from_filename(filename: str):
    """
    Intenta obtener artista y título a partir del nombre del archivo.

    Ejemplo:
        "Avicii - The Nights (Lyric Video).mp3"

    Resultado:
        {
            "artist": "Avicii",
            "title": "The Nights (Lyric Video)",
            "confidence": 0.90
        }
    """

    if not filename:
        return {
            "artist": None,
            "title": None,
            "confidence": 0.0
        }

    # Quitar extensión
    name = re.sub(
        r"\.(mp3|flac|wav|m4a|ogg)$",
        "",
        filename,
        flags=re.IGNORECASE
    )

    name = clean_extracted_text(name)

    if not name:
        return {
            "artist": None,
            "title": None,
            "confidence": 0.0
        }

    # Buscar separadores típicos:
    #
    # Avicii - The Nights
    # Avicii – The Nights
    # Avicii — The Nights
    # Avicii _ The Nights

    match = re.match(
        r"^(.+?)\s*[-–—_]\s*(.+)$",
        name
    )

    if match:
        artist = clean_extracted_text(match.group(1))
        title = clean_extracted_text(match.group(2))

        if artist and title:
            return {
                "artist": artist,
                "title": title,
                "confidence": 0.90
            }

    # Si no encontramos separador,
    # dejamos los campos sin inferir.
    return {
        "artist": None,
        "title": name,
        "confidence": 0.40
    }
    
if __name__ == "__main__":
    tests = [
        "Avicii - The Nights.mp3",
        "Avicii - Waiting For Love (Lyric Video).mp3",
        "Avicii - Lonely Together “Audio” ft. Rita Ora.mp3",
        "Broken Arrows.mp3",
        "Hey Brother.mp3",
    ]

    for filename in tests:
        result = extract_artist_title_from_filename(filename)

        print(f"\nArchivo: {filename}")
        print(f"Artista: {result['artist']}")
        print(f"Título: {result['title']}")
        print(f"Confianza: {result['confidence']}")