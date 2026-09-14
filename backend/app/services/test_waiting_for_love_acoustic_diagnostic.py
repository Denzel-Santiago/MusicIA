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

        print(
            "MusicAI - diagnóstico acústico"
        )
        print("=" * 75)

        print("Canción local")
        print("-" * 75)
        print(f"ID: {song.id}")
        print(f"Archivo: {song.file_path}")
        print(f"Título: {song.title}")
        print(f"Artista: {song.artist}")
        print(
            f"Duración SQLite: "
            f"{song.duration} segundos"
        )
        print(
            f"Fingerprint: "
            f"{len(song.acoustic_fingerprint)} caracteres"
        )
        print()

        acoustid_client = create_acoustid_client(
            api_key
        )

        musicbrainz_client = (
            create_musicbrainz_client()
        )

        print(
            "Consultando AcoustID..."
        )
        print()

        response = acoustid_client.lookup(
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
            meta="recordingids",
        )

        results = response.get(
            "results",
            [],
        )

        print(
            f"Resultados AcoustID: "
            f"{len(results)}"
        )
        print()

        if not results:
            print(
                "⚠️ AcoustID no devolvió resultados."
            )
            return

        for index, result in enumerate(
            results,
            start=1,
        ):
            acoustid = result.get("id")
            score = result.get("score")

            recordings = result.get(
                "recordings",
                [],
            )

            print(
                f"RESULTADO ACOUSTID #{index}"
            )
            print("-" * 75)
            print(
                f"AcoustID: {acoustid}"
            )
            print(
                f"Score: {score}"
            )

            if not recordings:
                print(
                    "MusicBrainz Recording IDs: "
                    "ninguno"
                )
                print()
                continue

            for recording_index, recording in enumerate(
                recordings,
                start=1,
            ):
                recording_id = recording.get(
                    "id"
                )

                print()
                print(
                    f"  Recording #{recording_index}"
                )
                print(
                    f"  MBID: {recording_id}"
                )

                if not recording_id:
                    continue

                print(
                    "  Consultando MusicBrainz..."
                )

                try:
                    mb_recording = (
                        musicbrainz_client.get_recording(
                            recording_id
                        )
                    )

                except Exception as exc:
                    print(
                        "  ❌ Error MusicBrainz: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                if not mb_recording:
                    print(
                        "  ⚠️ MusicBrainz no devolvió "
                        "información."
                    )
                    continue

                print(
                    f"  Título: "
                    f"{mb_recording.get('title')}"
                )
                print(
                    f"  Artista: "
                    f"{mb_recording.get('artist')}"
                )
                print(
                    f"  Duración: "
                    f"{mb_recording.get('duration')}"
                )

            print()

        print("=" * 75)
        print(
            "Diagnóstico terminado."
        )
        print(
            "SQLite no fue modificado."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()