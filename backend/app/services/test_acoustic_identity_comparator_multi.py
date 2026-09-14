from __future__ import annotations

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

from app.services.metadata_resolver import (
    resolve_metadata,
)
from app.services.metadata_cleaner import clean_title


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")


TEST_SONG_IDS = [
    1,
    32,
    35,
    39,
    40,
]


def main() -> None:
    api_key = os.getenv("ACOUSTID_API_KEY")

    if not api_key:
        print(
            "❌ No se encontró ACOUSTID_API_KEY en .env"
        )
        return

    db = SessionLocal()

    try:
        acoustid_client = create_acoustid_client(
            api_key
        )

        musicbrainz_client = create_musicbrainz_client()

        songs = (
            db.query(Song)
            .filter(Song.id.in_(TEST_SONG_IDS))
            .order_by(Song.id)
            .all()
        )

        print(
            "MusicAI - prueba multi-canción "
            "del comparador acústico"
        )

        print("=" * 70)

        print(
            f"Canciones solicitadas: "
            f"{len(TEST_SONG_IDS)}"
        )

        print(
            f"Canciones encontradas: "
            f"{len(songs)}"
        )

        print()

        results = []

        for index, song in enumerate(songs, start=1):

            print(
                f"[{index}/{len(songs)}] "
                f"ID {song.id}: "
                f"{song.title or '(sin título)'}"
            )

            print("-" * 70)

            if not song.acoustic_fingerprint:
                print(
                    "❌ Sin fingerprint acústico. "
                    "Se omite."
                )
                print()
                continue

            if song.duration is None:
                print(
                    "❌ Sin duración. "
                    "Se omite."
                )
                print()
                continue

            # -------------------------------------------------
            # 1. Metadata original
            # -------------------------------------------------

            original_metadata = {
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "genre": song.genre,
                "year": song.year,
                "duration": song.duration,

                # Importante:
                # el scanner ya sabe si el título provino
                # de metadata o de un fallback del archivo.
                #
                # Para este test usamos la información
                # disponible en SQLite.
                "title_source": (
                    "filename_fallback"
                    if song.title
                    and song.title == Path(
                        song.file_path
                    ).stem
                    else "metadata"
                ),
            }
            
            cleaned_metadata = dict(original_metadata)
            cleaned_metadata["title"] = clean_title(
                original_metadata.get("title")
            )

            

            # -------------------------------------------------
            # 3. Resolver metadata mediante MusicAI
            # -------------------------------------------------

            resolved_metadata = resolve_metadata(
                metadata=cleaned_metadata,
                filename=Path(
                    song.file_path
                ).name,
            )

            local_identity = {
                "title": resolved_metadata.get(
                    "title"
                ),
                "artist": resolved_metadata.get(
                    "artist"
                ),
                "duration": song.duration,
            }

            print("Metadata original:")

            print(
                f"  Artista: "
                f"{original_metadata.get('artist')}"
            )

            print(
                f"  Título: "
                f"{original_metadata.get('title')}"
            )

            print()

            print("Metadata después de limpieza:")

            print(
                f"  Artista: "
                f"{cleaned_metadata.get('artist')}"
            )

            print(
                f"  Título: "
                f"{cleaned_metadata.get('title')}"
            )

            print()

            print("Identidad resuelta por MusicAI:")

            print(
                f"  Artista: "
                f"{local_identity.get('artist')}"
            )

            print(
                f"  Título: "
                f"{local_identity.get('title')}"
            )

            print(
                f"  Fuente: "
                f"{resolved_metadata.get('metadata_source')}"
            )

            print(
                f"  Confianza: "
                f"{resolved_metadata.get('metadata_confidence')}"
            )

            print(
                f"  Estado: "
                f"{resolved_metadata.get('resolution_status')}"
            )

            # -------------------------------------------------
            # 4. Identidad acústica
            # -------------------------------------------------

            try:

                acoustic_metadata = (
                    resolve_acoustic_metadata(
                        acoustid_client=acoustid_client,
                        musicbrainz_client=musicbrainz_client,
                        fingerprint=(
                            song.acoustic_fingerprint
                        ),
                        duration=song.duration,
                        local_metadata=local_identity,
                    )
                )

                print()

                print("Identidad acústica:")

                print(
                    f"  Artista: "
                    f"{acoustic_metadata.get('artist')}"
                )

                print(
                    f"  Título: "
                    f"{acoustic_metadata.get('title')}"
                )

                print(
                    f"  Score AcoustID: "
                    f"{acoustic_metadata.get('acoustid_score')}"
                )

                print(
                    f"  Score candidato: "
                    f"{acoustic_metadata.get('candidate_score')}"
                )

                print(
                    f"  Estado: "
                    f"{acoustic_metadata.get('status')}"
                )

                # -------------------------------------------------
                # 5. Comparar identidad resuelta vs acústica
                # -------------------------------------------------

                comparison = compare_acoustic_identity(
                    local_metadata=local_identity,
                    acoustic_metadata=acoustic_metadata,
                )

                results.append(
                    {
                        "id": song.id,
                        "classification": (
                            comparison[
                                "classification"
                            ]
                        ),
                        "decision": (
                            comparison[
                                "decision"
                            ]
                        ),
                        "overall_similarity": (
                            comparison[
                                "overall_similarity"
                            ]
                        ),
                        "acoustic_score": (
                            comparison[
                                "acoustic_score"
                            ]
                        ),
                    }
                )

                print()

                print("Resultado:")

                print(
                    f"  Clasificación: "
                    f"{comparison['classification']}"
                )

                print(
                    f"  Decisión: "
                    f"{comparison['decision']}"
                )

                print(
                    f"  Similitud título: "
                    f"{comparison['title_similarity']}"
                )

                print(
                    f"  Similitud artista: "
                    f"{comparison['artist_similarity']}"
                )

                print(
                    f"  Similitud general: "
                    f"{comparison['overall_similarity']}"
                )

                print()

                print("  Motivo:")

                print(
                    f"  {comparison['reason']}"
                )

            except AcousticIdentityComparatorError as exc:

                print(
                    f"❌ Error del comparador: {exc}"
                )

            except Exception as exc:

                print(
                    f"❌ Error inesperado: "
                    f"{type(exc).__name__}: {exc}"
                )

            print()

        print("=" * 70)

        print("RESUMEN")

        print("=" * 70)

        for result in results:

            print(
                f"ID {result['id']:>2} | "
                f"{result['classification']:<10} | "
                f"{result['decision']:<28} | "
                f"similitud="
                f"{result['overall_similarity']} | "
                f"AcoustID="
                f"{result['acoustic_score']}"
            )

        print()

        print("=" * 70)

        print("SQLite no fue modificado.")

    finally:
        db.close()


if __name__ == "__main__":
    main()

