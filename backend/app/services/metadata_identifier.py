"""Local song identification primitives with no external dependencies."""

from copy import deepcopy


IDENTIFICATION_SOURCE = "local"


def _first_available(metadata, normalized_key, original_key):
    """Prefer an interpreted value while retaining the original as fallback."""
    return metadata.get(normalized_key) or metadata.get(original_key)


def _status_and_confidence(title, artist):
    """Assess only the information supplied by the caller."""
    if title and artist:
        return "identified", 0.9

    if title:
        return "partial", 0.5

    if artist:
        return "partial", 0.4

    return "unidentified", 0.0


def identify_song(metadata):
    """Identify a song from local metadata without changing the input mapping.

    The return value intentionally includes an empty ``external_ids`` mapping.
    Future providers may populate it without changing this local contract.
    """
    title = _first_available(metadata, "normalized_title", "title")
    artist = _first_available(metadata, "normalized_artist", "artist")
    status, confidence = _status_and_confidence(title, artist)

    return {
        "title": title,
        "artist": artist,
        "album": metadata.get("album"),
        "year": metadata.get("year"),
        "duration": metadata.get("duration"),
        "confidence": confidence,
        "source": IDENTIFICATION_SOURCE,
        "status": status,
        "external_ids": {},
    }


if __name__ == "__main__":
    tests = (
        ("Complete local metadata", {"title": "The Nights", "artist": "Avicii"}),
        ("Title only", {"title": "The Nights", "artist": None}),
        ("Unknown artist", {"title": "Broken Arrows", "artist": None}),
        ("No identifying metadata", {"title": None, "artist": None}),
        (
            "Featured artist",
            {"title": "Without You", "artist": "Avicii Feat. Sandro Cavazza"},
        ),
        ("Another complete song", {"title": "For A Better Day", "artist": "Avicii"}),
        (
            "Normalized values take priority",
            {
                "title": "The Nights (Lyric Video)",
                "artist": "Avicii",
                "normalized_title": "The Nights",
                "normalized_artist": "Avicii",
                "album": "Stories",
                "year": 2015,
                "duration": 177.0,
            },
        ),
    )

    for name, metadata in tests:
        original_metadata = deepcopy(metadata)
        result = identify_song(metadata)
        unchanged = metadata == original_metadata

        print("\n-----------------------------")
        print(f"Caso: {name}")
        print(f"Resultado: {result}")
        print(f"Entrada sin cambios: {'OK' if unchanged else 'ERROR'}")
