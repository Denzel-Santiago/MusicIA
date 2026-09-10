from __future__ import annotations

from app.services.musicbrainz_client import create_musicbrainz_client


def main() -> None:
    client = create_musicbrainz_client()

    print("=" * 90)
    print("PRUEBA DIRECTA DE MUSICBRAINZ - THE NIGHTS / AVICII")
    print("=" * 90)

    print()
    print("Consulta:")
    print("  Título: The Nights")
    print("  Artista: Avicii")

    print()
    print("Consultando MusicBrainz...")
    print("-" * 90)

    results = client.search_recordings(
        title="The Nights",
        artist="Avicii",
        limit=5,
    )

    print()
    print(f"Resultados recibidos: {len(results)}")

    print()

    if not results:
        print("MusicBrainz no devolvió resultados.")
        print()
        print("=" * 90)
        print("FIN")
        print("=" * 90)
        return

    for index, result in enumerate(results, start=1):

        print("-" * 90)
        print(f"CANDIDATO #{index}")
        print("-" * 90)

        print(f"MBID:       {result.get('mbid')}")
        print(f"Título:     {result.get('title')!r}")
        print(f"Artista:    {result.get('artist')!r}")
        print(f"Artistas:   {result.get('artists')!r}")
        print(f"Duración:   {result.get('duration')}")

    print()
    print("=" * 90)
    print("FIN DE LA PRUEBA")
    print("=" * 90)


if __name__ == "__main__":
    main()