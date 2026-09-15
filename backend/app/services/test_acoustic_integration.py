
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song

from app.services.acoustid_client import create_acoustid_client
from app.services.musicbrainz_client import MusicBrainzClient

from app.services.acoustic_fingerprint import generate_fingerprint
from app.services.acoustic_metadata_resolver import (
    resolve_acoustic_metadata,
)
from app.services.acoustic_identity_comparator import (
    compare_acoustic_identity,
)

from app.services.metadata_cleaner import clean_title
from app.services.metadata_resolver import resolve_metadata


# ============================================================
# CONFIGURACIÓN
# ============================================================

TEST_SONG_IDS = [1, 32, 35, 39, 40]


# ============================================================
# VARIABLES DE ENTORNO
# ============================================================

load_dotenv()


# ============================================================
# CONSTRUIR METADATA LOCAL
# ============================================================

def build_local_metadata(song: Song) -> dict:
    """
    Construye la identidad local que MusicAI utilizaría
    antes de compararla con la identidad acústica.

    El objetivo es reproducir el pipeline real de MusicAI:

        metadata original
                ↓
        limpieza del título
                ↓
        análisis del filename
                ↓
        resolución de metadata
                ↓
        identidad local final
    """

    original_metadata = {
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "genre": song.genre,
        "year": song.year,
        "duration": song.duration,
    }

    # --------------------------------------------------------
    # Obtener filename sin extensión
    # --------------------------------------------------------

    filename = Path(song.file_path).stem

    # --------------------------------------------------------
    # Limpiar título original
    # --------------------------------------------------------

    cleaned_title = clean_title(
        original_metadata.get("title")
    )

    cleaned_metadata = {
        **original_metadata,
        "title": cleaned_title,
    }

    # --------------------------------------------------------
    # Resolver metadata usando el mismo resolver
    # utilizado por MusicAI
    # --------------------------------------------------------

    resolved = resolve_metadata(
        cleaned_metadata,
        filename,
    )

    return {
        "title": resolved.get("title"),
        "artist": resolved.get("artist"),
        "duration": resolved.get("duration"),
    }


# ============================================================
# PRUEBA PRINCIPAL
# ============================================================

def run_test():

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Inicializar AcoustID
        # ----------------------------------------------------

        api_key = os.getenv("ACOUSTID_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró ACOUSTID_API_KEY "
                "en el archivo .env"
            )

        acoustid_client = create_acoustid_client(
            api_key
        )

        # ----------------------------------------------------
        # Inicializar MusicBrainz
        # ----------------------------------------------------

        musicbrainz_client = MusicBrainzClient()

        # ----------------------------------------------------
        # Obtener canciones
        # ----------------------------------------------------

        songs = (
            db.query(Song)
            .filter(
                Song.id.in_(TEST_SONG_IDS)
            )
            .order_by(
                Song.id
            )
            .all()
        )

        if not songs:

            print(
                "No se encontraron canciones "
                "para la prueba."
            )

            return

        passed = 0

        print(
            "\n=============================================="
        )

        print(
            "TEST DE INTEGRACIÓN ACÚSTICA COMPLETA"
        )

        print(
            "==============================================\n"
        )

        # ====================================================
        # PROBAR CADA CANCIÓN
        # ====================================================

        for song in songs:

            print(
                "----------------------------------------------"
            )

            print(
                f"ID: {song.id}"
            )

            print(
                f"Archivo: {song.file_path}"
            )

            print(
                "----------------------------------------------"
            )

            try:

                # =================================================
                # 1. METADATA LOCAL
                # =================================================

                local_metadata = build_local_metadata(
                    song
                )

                print(
                    "\n[1] Metadata local"
                )

                print(
                    f"  Título:  "
                    f"{local_metadata.get('title')}"
                )

                print(
                    f"  Artista: "
                    f"{local_metadata.get('artist')}"
                )

                print(
                    f"  Duración: "
                    f"{local_metadata.get('duration')}"
                )

                # =================================================
                # 2. FINGERPRINT
                # =================================================

                print(
                    "\n[2] Generando fingerprint..."
                )

                fingerprint_data = generate_fingerprint(
                    song.file_path
                )

                fingerprint = fingerprint_data[
                    "fingerprint"
                ]

                fingerprint_duration = fingerprint_data[
                    "duration"
                ]

                print(
                    f"  Fingerprint generado: "
                    f"{len(fingerprint)} caracteres"
                )

                print(
                    f"  Duración fingerprint: "
                    f"{fingerprint_duration}"
                )

                # =================================================
                # 3. ACOUSTID + MUSICBRAINZ
                # =================================================

                print(
                    "\n[3] Consultando identidad acústica..."
                )

                acoustic_metadata = resolve_acoustic_metadata(
                    fingerprint=fingerprint,
                    duration=fingerprint_duration,
                    acoustid_client=acoustid_client,
                    musicbrainz_client=musicbrainz_client,
                    local_metadata=local_metadata,
                )

                print(
                    f"  Estado: "
                    f"{acoustic_metadata.get('status')}"
                )

                print(
                    f"  AcoustID score: "
                    f"{acoustic_metadata.get('acoustid_score')}"
                )

                print(
                    f"  MBID: "
                    f"{acoustic_metadata.get('musicbrainz_recording_id')}"
                )

                print(
                    f"  Título acústico: "
                    f"{acoustic_metadata.get('title')}"
                )

                print(
                    f"  Artista acústico: "
                    f"{acoustic_metadata.get('artist')}"
                )

                # =================================================
                # 4. COMPARACIÓN DE IDENTIDAD
                # =================================================

                print(
                    "\n[4] Comparando identidades..."
                )

                comparison = (
                    compare_acoustic_identity(
                        local_metadata=local_metadata,
                        acoustic_metadata=acoustic_metadata,
                    )
                )

                print(
                    f"  Similitud título: "
                    f"{comparison.get('title_similarity')}"
                )

                print(
                    f"  Similitud artista: "
                    f"{comparison.get('artist_similarity')}"
                )

                print(
                    f"  Similitud general: "
                    f"{comparison.get('overall_similarity')}"
                )

                print(
                    f"  Clasificación: "
                    f"{comparison.get('classification')}"
                )

                print(
                    f"  Decisión: "
                    f"{comparison.get('decision')}"
                )

                print(
                    f"  Razón: "
                    f"{comparison.get('reason')}"
                )

                # =================================================
                # 5. EVALUACIÓN
                # =================================================

                success = (
                    acoustic_metadata.get("status")
                    == "identified"
                    and comparison.get("classification")
                    == "confirmed"
                    and comparison.get("decision")
                    == "identity_confirmed"
                )

                if success:

                    print(
                        "\n  RESULTADO: PASS"
                    )

                    passed += 1

                else:

                    print(
                        "\n  RESULTADO: FAIL"
                    )

            except Exception as exc:

                print(
                    "\n  RESULTADO: ERROR"
                )

                print(
                    f"  {type(exc).__name__}: {exc}"
                )

        # ====================================================
        # RESULTADO FINAL
        # ====================================================

        print(
            "\n=============================================="
        )

        print(
            f"RESULTADO FINAL: "
            f"{passed}/{len(songs)} canciones confirmadas"
        )

        print(
            "==============================================\n"
        )

    finally:

        db.close()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    run_test()
