from pathlib import Path
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import create_acoustid_client
from app.services.acoustic_identifier import (
    identify_by_fingerprint,
    AcousticIdentifierError,
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

        print("MusicAI - prueba de identificación acústica")
        print("=" * 55)
        print(f"ID: {song.id}")
        print(f"Título local: {song.title}")
        print(f"Artista local: {song.artist}")
        print(f"Duración: {song.duration}")
        print()

        client = create_acoustid_client(api_key)

        result = identify_by_fingerprint(
            client=client,
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print("Resultado:")
        print("=" * 55)
        print(f"Estado: {result['status']}")
        print(f"AcoustID: {result['acoustid']}")
        print(f"Score: {result['score']}")

        print("MusicBrainz Recording IDs:")

        recording_ids = result["musicbrainz_recording_ids"]

        if recording_ids:
            for recording_id in recording_ids:
                print(f"  - {recording_id}")
        else:
            print("  Ninguno")

    except AcousticIdentifierError as exc:
        print("❌ Error:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()