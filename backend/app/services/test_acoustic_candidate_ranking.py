from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import (
    create_acoustid_client,
)
from app.services.musicbrainz_client import (
    create_musicbrainz_client,
)
from app.services.acoustic_identifier import (
    rank_acoustic_candidates,
)
from app.services.filename_parser import (
    extract_artist_title_from_filename,
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

        filename_result = (
            extract_artist_title_from_filename(
                Path(song.file_path).name
            )
        )

        local_metadata = {
            "title": filename_result.get(
                "title"
            ),
            "artist": filename_result.get(
                "artist"
            ),
            "duration": song.duration,
        }

        acoustid_client = create_acoustid_client(
            api_key
        )

        musicbrainz_client = (
            create_musicbrainz_client()
        )

        print(
            "MusicAI - ranking de candidatos acústicos"
        )
        print("=" * 75)

        print("Canción local")
        print("-" * 75)
        print(f"ID: {song.id}")
        print(f"Archivo: {song.file_path}")
        print(
            f"Título detectado: "
            f"{local_metadata['title']}"
        )
        print(
            f"Artista detectado: "
            f"{local_metadata['artist']}"
        )
        print(
            f"Duración: "
            f"{local_metadata['duration']}"
        )
        print()

        print(
            "Analizando candidatos..."
        )
        print()

        candidates = rank_acoustic_candidates(
            client=acoustid_client,
            musicbrainz_client=musicbrainz_client,
            local_metadata=local_metadata,
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print(
            f"Candidatos MusicBrainz analizados: "
            f"{len(candidates)}"
        )
        print()

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"#{index} "
                f"{candidate['title']} "
                f"— "
                f"{candidate['artist']}"
            )

            print(
                f"   MBID: "
                f"{candidate['musicbrainz_recording_id']}"
            )

            print(
                f"   AcoustID: "
                f"{candidate['acoustid_score']}"
            )

            print(
                f"   Título: "
                f"{candidate['title_similarity']}"
            )

            print(
                f"   Artista: "
                f"{candidate['artist_similarity']}"
            )

            print(
                f"   Duración: "
                f"{candidate['duration_similarity']}"
            )

            print(
                f"   Metadata score: "
                f"{candidate['metadata_score']}"
            )

            print(
                f"   SCORE FINAL: "
                f"{candidate['final_score']}"
            )

            print()

        print("=" * 75)

        if candidates:
            best = candidates[0]

            print("MEJOR CANDIDATO")
            print("-" * 75)
            print(
                f"Título: "
                f"{best['title']}"
            )
            print(
                f"Artista: "
                f"{best['artist']}"
            )
            print(
                f"MBID: "
                f"{best['musicbrainz_recording_id']}"
            )
            print(
                f"Score final: "
                f"{best['final_score']}"
            )

        print()
        print("=" * 75)
        print("SQLite no fue modificado.")

    finally:
        db.close()


if __name__ == "__main__":
    main()