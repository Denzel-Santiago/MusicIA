import re


def clean_text(value):
    """
    Limpia espacios innecesarios sin alterar significativamente
    el contenido original.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    value = re.sub(r"\s+", " ", value)

    return value


def normalize_artist(value):
    """
    Normaliza el nombre del artista.
    """

    value = clean_text(value)

    if value is None:
        return None

    return value


def normalize_title(value):
    """
    Normaliza el título.
    """

    value = clean_text(value)

    if value is None:
        return None

    return value


def normalize_album(value):
    """
    Normaliza el nombre del álbum.
    """

    value = clean_text(value)

    if value is None:
        return None

    return value


def normalize_genre(value):
    """
    Normaliza el género.
    """

    value = clean_text(value)

    if value is None:
        return None

    return value


def normalize_metadata(metadata):
    return {
        "title": normalize_title(metadata.get("title")),
        "artist": normalize_artist(metadata.get("artist")),
        "album": normalize_album(metadata.get("album")),
        "genre": normalize_genre(metadata.get("genre")),
        "year": metadata.get("year"),
        "duration": metadata.get("duration"),
        "title_source": metadata.get("title_source"),
    }