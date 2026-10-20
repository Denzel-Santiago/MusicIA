from __future__ import annotations

import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import create_acoustid_client
from app.services.acoustic_fingerprint import generate_fingerprint
from app.services.acoustic_identifier import (
    identify_by_fingerprint,
    get_acoustic_candidates,
)
from app.services.musicbrainz_client import MusicBrainzClient


SONG_ID = 35

load_dotenv()


def run_test():
    db = SessionLocal()

    try:
        api_key = os.getenv("ACOUSTID_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró ACOUSTID_API_KEY en el archivo .env"
            )

        song = (
            db.query(Song)
            .filter(Song.id == SONG_ID)
            .first()
        )

        if not song:
            print(f"No se encontró la canción con ID {SONG_ID}.")
            return

        print("=" * 60)
        print("ANÁLISIS DE CANDIDATOS ACOUSTID - WAITING FOR LOVE")
        print("=" * 60)

        print()
        print("Canción local:")
        print(f"  ID: {song.id}")
        print(f"  Título: {song.title}")
        print(f"  Artista: {song.artist}")
        print(f"  Archivo: {song.file_path}")

        print()
        print("Generando fingerprint...")

        fingerprint_data = generate_fingerprint(song.file_path)

        fingerprint = fingerprint_data["fingerprint"]
        duration = fingerprint_data["duration"]

        print(f"  Duración: {duration}")
        print(f"  Fingerprint: {len(fingerprint)} caracteres")

        acoustid_client = create_acoustid_client(api_key)
        musicbrainz_client = MusicBrainzClient()

        # --------------------------------------------------
        # 1. Identificación básica mediante AcoustID
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("1. RESULTADO DIRECTO DE ACOUSTID")
        print("=" * 60)

        acoustic_result = identify_by_fingerprint(
            client=acoustid_client,
            fingerprint=fingerprint,
            duration=duration,
        )

        print()
        print(f"Estado: {acoustic_result.get('status')}")
        print(f"AcoustID: {acoustic_result.get('acoustid')}")
        print(f"Score: {acoustic_result.get('score')}")

        recording_ids = acoustic_result.get(
            "musicbrainz_recording_ids",
            [],
        )

        print()
        print("MusicBrainz Recording IDs encontrados:")

        if not recording_ids:
            print("  Ninguno")
        else:
            for index, recording_id in enumerate(
                recording_ids,
                start=1,
            ):
                print(f"  {index}. {recording_id}")

        # --------------------------------------------------
        # 2. Todos los candidatos devueltos por AcoustID
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("2. TODOS LOS CANDIDATOS ACOUSTID")
        print("=" * 60)

        candidates = get_acoustic_candidates(
            client=acoustid_client,
            fingerprint=fingerprint,
            duration=duration,
        )

        print()
        print(f"Total de candidatos: {len(candidates)}")

        if not candidates:
            print("No se encontraron candidatos.")
            return

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print()
            print(f"CANDIDATO #{index}")
            print(
                f"  AcoustID: "
                f"{candidate.get('acoustid')}"
            )
            print(
                f"  AcoustID score: "
                f"{candidate.get('acoustid_score')}"
            )
            print(
                f"  MBID: "
                f"{candidate.get('musicbrainz_recording_id')}"
            )

        # --------------------------------------------------
        # 3. Consultar cada MBID directamente
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("3. INFORMACIÓN MUSICBRAINZ DE CADA CANDIDATO")
        print("=" * 60)

        processed_mbids = set()

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            recording_id = candidate.get(
                "musicbrainz_recording_id"
            )

            if not recording_id:
                continue

            if recording_id in processed_mbids:
                continue

            processed_mbids.add(recording_id)

            print()
            print(f"CANDIDATO #{index}")
            print(f"  MBID: {recording_id}")
            print(
                f"  AcoustID score: "
                f"{candidate.get('acoustid_score')}"
            )

            try:
                recording = (
                    musicbrainz_client.get_recording(
                        recording_id
                    )
                )

                if not recording:
                    print(
                        "  MusicBrainz no devolvió "
                        "información."
                    )
                    continue

                print(
                    f"  Título: "
                    f"{recording.get('title')}"
                )

                print(
                    f"  Artista: "
                    f"{recording.get('artist')}"
                )

                print(
                    f"  Duración: "
                    f"{recording.get('duration')}"
                )

                print(
                    f"  Artistas: "
                    f"{recording.get('artists')}"
                )

            except Exception as exc:
                print(
                    f"  ERROR MusicBrainz: "
                    f"{type(exc).__name__}: {exc}"
                )

        # --------------------------------------------------
        # 4. Ranking real de MusicAI
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("4. RANKING ACTUAL DE MUSICAI")
        print("=" * 60)

        from app.services.acoustic_identifier import (
            rank_acoustic_candidates,
        )

        # Importante:
        # usamos la identidad LOCAL ya corregida,
        # no la metadata cruda de SQLite.

        local_metadata = {
            "title": "Waiting For Love",
            "artist": "Avicii",
            "duration": duration,
        }

        ranked = rank_acoustic_candidates(
            client=acoustid_client,
            musicbrainz_client=musicbrainz_client,
            local_metadata=local_metadata,
            fingerprint=fingerprint,
            duration=duration,
        )

        print()
        print(
            f"Total de candidatos analizados: "
            f"{len(ranked)}"
        )

        for index, candidate in enumerate(
            ranked,
            start=1,
        ):
            print()
            print(f"RANKING #{index}")

            print(
                f"  Título: "
                f"{candidate.get('title')}"
            )

            print(
                f"  Artista: "
                f"{candidate.get('artist')}"
            )

            print(
                f"  MBID: "
                f"{candidate.get('musicbrainz_recording_id')}"
            )

            print(
                f"  AcoustID score: "
                f"{candidate.get('acoustid_score')}"
            )

            print(
                f"  Similitud título: "
                f"{candidate.get('title_similarity')}"
            )

            print(
                f"  Similitud artista: "
                f"{candidate.get('artist_similarity')}"
            )

            print(
                f"  Similitud duración: "
                f"{candidate.get('duration_similarity')}"
            )

            print(
                f"  Metadata score: "
                f"{candidate.get('metadata_score')}"
            )

            print(
                f"  FINAL SCORE: "
                f"{candidate.get('final_score')}"
            )

            print(
                f"  Estado: "
                f"{candidate.get('status')}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    run_test()