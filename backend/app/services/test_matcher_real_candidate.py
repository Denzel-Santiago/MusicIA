from __future__ import annotations

from app.services.metadata_matcher import rank_candidates


def main() -> None:
    metadata = {
        "title": "The Nights",
        "artist": "Avicii",
        "duration": 175.72571428571428,
    }

    candidates = [
        {
            "mbid": "42be64b8-18a1-4782-8937-659a537c613f",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 198.16,
        },
        {
            "mbid": "c365e2d0-ac24-456e-bc8e-aec044fc3337",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": None,
        },
        {
            "mbid": "1b1e4b65-9b1a-48cd-8e3a-b4824f15bf0c",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 177.0,
        },
        {
            "mbid": "d2bae379-906c-4eca-8f65-78c1adcee379",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 173.292,
        },
        {
            "mbid": "5788747a-14f9-41bb-8f29-eb8f7c0498db",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 246.973,
        },
    ]

    print("=" * 90)
    print("PRUEBA REAL DEL MATCHER - THE NIGHTS / AVICII")
    print("=" * 90)

    print()
    print("METADATA LOCAL")
    print("-" * 90)
    print(f"Título:   {metadata['title']!r}")
    print(f"Artista:  {metadata['artist']!r}")
    print(f"Duración: {metadata['duration']}")

    print()
    print("EJECUTANDO MATCHER...")
    print("-" * 90)

    results = rank_candidates(
        metadata,
        candidates,
    )

    print()

    for index, result in enumerate(results, start=1):
        print("-" * 90)
        print(f"RESULTADO #{index}")
        print("-" * 90)

        print(f"MBID:                 {result.get('mbid')}")
        print(f"Título:               {result.get('title')!r}")
        print(f"Artista:              {result.get('artist')!r}")
        print(f"Duración:             {result.get('duration')}")
        print(f"Score:                {result.get('score')}")
        print(f"Clasificación:        {result.get('classification')}")
        print(f"Similitud título:     {result.get('title_similarity')}")
        print(f"Similitud artista:    {result.get('artist_similarity')}")
        print(f"Similitud duración:   {result.get('duration_similarity')}")

    print()
    print("=" * 90)
    print("FIN DE LA PRUEBA")
    print("=" * 90)


if __name__ == "__main__":
    main()