from app.services.metadata_resolver import resolve_metadata
from app.services.metadata_identifier import (
    _build_external_query_candidates,
)


TEST_CASES = [
    {
        "name": "Hablame De Ti",
        "filename": "(Letra) Hablame De Ti - Banda MS (Completa).mp3",
        "metadata": {
            "title": "Banda MS (Completa)",
            "artist": "(Letra) Hablame De Ti",
            "album": None,
            "genre": None,
            "year": None,
            "duration": 190.98122448979592,
            "title_source": "metadata",
        },
    },
    {
        "name": "Avicii Coldplay",
        "filename": "Avicii & Coldplay   We Are NEW SONG 2017.mp3",
        "metadata": {
            "title": "Avicii & Coldplay We Are NEW SONG 2017",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": None,
            "title_source": "filename_fallback",
        },
    },
        {
        "name": "The Nights",
        "filename": "Avicii - The Nights.mp3",
        "metadata": {
            "title": "Avicii - The Nights",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 175.72571428571428,
            "title_source": "metadata",
        },
    },
]


for case in TEST_CASES:
    print("=" * 70)
    print(case["name"])
    print("=" * 70)

    resolved = resolve_metadata(
        case["metadata"],
        case["filename"],
    )

    print("\nResolución local:")
    print("Título:", resolved.get("title"))
    print("Artista:", resolved.get("artist"))
    print("Estado:", resolved.get("resolution_status"))
    print("Confianza:", resolved.get("metadata_confidence"))

    print("\nCalidad:")
    quality = resolved.get("quality", {})
    print("Estado:", quality.get("status"))
    print("Confianza:", quality.get("confidence"))
    print("Ruido:", quality.get("content_noise"))

    candidates = _build_external_query_candidates(
        resolved,
        case["filename"],
    )

    print("\nCandidatos para MusicBrainz:")

    if not candidates:
        print("  ❌ No se generaron candidatos.")
    else:
        for index, candidate in enumerate(candidates, start=1):
            print(f"  {index}.")
            print(f"     Título:  {candidate['title']}")
            print(f"     Artista: {candidate['artist']}")
            print(f"     Razón:   {candidate['reason']}")

    print()