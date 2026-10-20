from app.services.musicbrainz_client import (
    create_musicbrainz_client,
)


RECORDING_ID = "1f7444ce-c7c6-4194-87d1-d463b2b0f0a2"


def main() -> None:
    print("MusicAI - consulta MusicBrainz por MBID")
    print("=" * 55)
    print(f"Recording MBID: {RECORDING_ID}")
    print()

    client = create_musicbrainz_client()

    print("Consultando MusicBrainz...")
    print()

    result = client.get_recording(RECORDING_ID)

    if result is None:
        print("❌ No se encontró el recording.")
        return

    print("✅ Recording encontrado")
    print()
    print(f"MBID: {result.get('mbid')}")
    print(f"Título: {result.get('title')}")
    print(f"Artista: {result.get('artist')}")
    print(f"Artistas: {result.get('artists')}")
    print(f"Duración: {result.get('duration')}")


if __name__ == "__main__":
    main()