from pathlib import Path
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import create_acoustid_client
from app.services.musicbrainz_client import create_musicbrainz_client
from app.services.acoustic_metadata_resolver import (
    resolve_acoustic_metadata,
)
from app.services.acoustic_identity_comparator import (
    compare_acoustic_identity,
    AcousticIdentityComparatorError,
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

        print("MusicAI - comparador de identidad acústica")
        print("=" * 60)

        print("Metadata local")
        print("-" * 60)
        print(f"Título: {song.title}")
        print(f"Artista: {song.artist}")
        print()

        acoustid_client = create_acoustid_client(
            api_key
        )

        musicbrainz_client = create_musicbrainz_client()

        print("Identificando mediante fingerprint...")
        print()

        acoustic_metadata = resolve_acoustic_metadata(
            acoustid_client=acoustid_client,
            musicbrainz_client=musicbrainz_client,
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print("Identidad acústica")
        print("-" * 60)
        print(
            f"Título: "
            f"{acoustic_metadata.get('title')}"
        )
        print(
            f"Artista: "
            f"{acoustic_metadata.get('artist')}"
        )
        print(
            f"Score AcoustID: "
            f"{acoustic_metadata.get('acoustid_score')}"
        )
        print()

        comparison = compare_acoustic_identity(
            local_metadata={
                "title": song.title,
                "artist": song.artist,
            },
            acoustic_metadata=acoustic_metadata,
        )

        print("Comparación")
        print("-" * 60)
        print(
            f"Clasificación: "
            f"{comparison['classification']}"
        )
        print(
            f"Decisión: "
            f"{comparison['decision']}"
        )
        print(
            f"Similitud título: "
            f"{comparison['title_similarity']}"
        )
        print(
            f"Similitud artista: "
            f"{comparison['artist_similarity']}"
        )
        print(
            f"Similitud general: "
            f"{comparison['overall_similarity']}"
        )
        print()
        print("Motivo:")
        print(comparison["reason"])

        print()
        print("SQLite no fue modificado.")

    except AcousticIdentityComparatorError as exc:
        print("❌ Error del comparador:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()