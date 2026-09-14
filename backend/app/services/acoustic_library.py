from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.song import Song
from app.services.acoustic_fingerprint_store import (
    AcousticFingerprintStoreError,
    generate_and_store_fingerprint,
)


def fingerprint_library(db: Session) -> dict[str, int]:
    """
    Genera fingerprints para las canciones disponibles que todavía
    no tienen uno almacenado.
    """

    songs = (
        db.query(Song)
        .filter(
            Song.is_available.is_(True),
            Song.acoustic_fingerprint.is_(None),
        )
        .order_by(Song.id)
        .all()
    )

    total = len(songs)
    processed = 0
    skipped = 0
    errors = 0

    print("MusicAI - fingerprinting de biblioteca")
    print("=" * 55)
    print(f"Canciones pendientes: {total}")
    print()

    for index, song in enumerate(songs, start=1):
        print(
            f"[{index}/{total}] "
            f"Procesando ID {song.id}: "
            f"{song.title or song.file_path}"
        )

        try:
            generate_and_store_fingerprint(db, song)
            processed += 1

            print("    ✅ Fingerprint guardado")

        except AcousticFingerprintStoreError as exc:
            errors += 1

            print(f"    ❌ Error: {exc}")

        except Exception as exc:
            errors += 1

            print(
                f"    ❌ Error inesperado: "
                f"{type(exc).__name__}: {exc}"
            )

    print()
    print("=" * 55)
    print("Resumen")
    print(f"Procesadas correctamente: {processed}")
    print(f"Omitidas: {skipped}")
    print(f"Errores: {errors}")

    return {
        "total": total,
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
    }