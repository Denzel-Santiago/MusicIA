from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import (
    create_acoustid_client,
)
from app.services.acoustic_identifier import (
    get_acoustic_candidates,
)


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")

SONG_ID = 35


def main() -> None:
    api_key = os.getenv("ACOUSTID_API_KEY")

    if not api_key:
        print(
            "❌ No se encontró ACOUSTID_API_KEY "
            "en .env"
        )
        return

    db = SessionLocal()

    try:
        song = (
            db.query(Song)
            .filter(Song.id == SONG_ID)
            .first()
        )

        if song is None:
            print(
                f"❌ No se encontró la canción "
                f"ID {SONG_ID}."
            )
            return

        if not song.acoustic_fingerprint:
            print(
                "❌ La canción no tiene "
                "fingerprint acústico."
            )
            return

        if song.duration is None:
            print(
                "❌ La canción no tiene duración."
            )
            return

        client = create_acoustid_client(api_key)

        print(
            "MusicAI - candidatos acústicos"
        )
        print("=" * 70)
        print(f"ID: {song.id}")
        print(f"Título local: {song.title}")
        print(f"Artista local: {song.artist}")
        print(f"Duración: {song.duration}")
        print()

        candidates = get_acoustic_candidates(
            client=client,
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print(
            f"Candidatos encontrados: "
            f"{len(candidates)}"
        )
        print()

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"[{index}] "
                f"AcoustID="
                f"{candidate['acoustid_score']}"
            )
            print(
                f"    AcoustID ID: "
                f"{candidate['acoustid']}"
            )
            print(
                f"    MBID: "
                f"{candidate['musicbrainz_recording_id']}"
            )
            print()

        print("=" * 70)
        print("SQLite no fue modificado.")

    finally:
        db.close()


if __name__ == "__main__":
    main()