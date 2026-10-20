from app.services.metadata_identifier import (
    identify_resolved_song,
)


TESTS = [
    {
        "name": "The Nights",
        "metadata": {
            "title": "Avicii - The Nights",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 198.16,
            "title_source": "filename_fallback",
        },
        "filename": "Avicii - The Nights.mp3",
    },
    {
        "name": "Waiting For Love",
        "metadata": {
            "title": "Waiting For Love",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 230.0,
            "title_source": "metadata",
        },
        "filename": "Avicii - Waiting For Love.mp3",
    },
    {
        "name": "Broken Arrows",
        "metadata": {
            "title": "Broken Arrows",
            "artist": "Avicii",
            "album": None,
            "genre": None,
            "year": None,
            "duration": 200.0,
            "title_source": "metadata",
        },
        "filename": "Broken Arrows.mp3",
    },
    {
        "name": "Hablame De Ti",
        "metadata": {
            "title": "Banda MS (Completa)",
            "artist": "(Letra) Hablame De Ti",
            "album": None,
            "genre": None,
            "year": None,
            "duration": 190.98,
            "title_source": "metadata",
        },
        "filename": "(Letra) Hablame De Ti - Banda MS (Completa).mp3",
    },
]


for test in TESTS:
    print("\n" + "=" * 60)
    print(test["name"])
    print("=" * 60)

    result = identify_resolved_song(
        metadata=test["metadata"],
        filename=test["filename"],
    )

    print("Título:", result["title"])
    print("Artista:", result["artist"])
    print("Confianza:", result["confidence"])
    print("Fuente:", result["source"])
    print("Estado:", result["status"])

    print("\nCalidad:")
    quality = result["resolution"]["quality"]
    print("  status:", quality["status"])
    print("  confidence:", quality["confidence"])
    print("  content_noise:", quality["content_noise"])

    print("\nVerificación externa:")
    verification = result["external_verification"]
    print("  needed:", verification["needed"])
    print("  query_ready:", verification["query_ready"])
    print("  attempted:", verification["attempted"])
    print("  reason:", verification["reason"])