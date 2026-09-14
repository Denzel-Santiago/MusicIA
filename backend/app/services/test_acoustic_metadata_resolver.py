from pathlib import Path
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import create_acoustid_client
from app.services.musicbrainz_client import create_musicbrainz_client
from app.services.acoustic_metadata_resolver import (
    resolve_acoustic_metadata,
    AcousticMetadataResolverError,
)


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")


def main() -> None:
    api_key = os.getenv("ACOUSTID_API_KEY")

    if not api_key:
        print("❌ No se encontró ACOUSTID_API_KEY en .env")
        return

    db = SessionLocal()

    try:
        song = (
            db.query(Song)
            .filter(Song.id == 1)
            .first()
        )

        if song is None:
            print("❌ No se encontró la canción ID 1.")
            return

        if not song.acoustic_fingerprint:
            print("❌ La canción no tiene fingerprint acústico.")
            return

        if song.duration is None:
            print("❌ La canción no tiene duración.")
            return

        print("MusicAI - resolución acústica completa")
        print("=" * 60)
        print(f"ID: {song.id}")
        print(f"Título local: {song.title}")
        print(f"Artista local: {song.artist}")
        print(f"Duración local: {song.duration}")
        print()

        acoustid_client = create_acoustid_client(
            api_key
        )

        musicbrainz_client = create_musicbrainz_client()

        print("Resolviendo identidad mediante fingerprint...")
        print()

        result = resolve_acoustic_metadata(
            acoustid_client=acoustid_client,
            musicbrainz_client=musicbrainz_client,
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print("Resultado")
        print("=" * 60)
        print(f"Estado: {result['status']}")
        print(f"AcoustID: {result['acoustid']}")
        print(
            f"Score AcoustID: "
            f"{result['acoustid_score']}"
        )
        print(
            f"MusicBrainz Recording ID: "
            f"{result['musicbrainz_recording_id']}"
        )
        print(f"Título identificado: {result['title']}")
        print(f"Artista identificado: {result['artist']}")
        print(
            f"Duración identificada: "
            f"{result['duration']}"
        )

        print()
        print("SQLite no fue modificado.")

    except AcousticMetadataResolverError as exc:
        print("❌ Error:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()