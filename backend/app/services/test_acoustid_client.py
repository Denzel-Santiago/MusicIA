from pathlib import Path
import json
import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.acoustid_client import (
    create_acoustid_client,
    AcoustIDClientError,
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

        print("MusicAI - inspección de respuesta AcoustID")
        print("=" * 55)
        print(f"ID: {song.id}")
        print(f"Título local: {song.title}")
        print(f"Artista local: {song.artist}")
        print(f"Duración: {song.duration}")
        print(
            f"Fingerprint: "
            f"{len(song.acoustic_fingerprint)} caracteres"
        )
        print()

        client = create_acoustid_client(api_key)

        print("Consultando AcoustID...")
        print()

        result = client.lookup(
            fingerprint=song.acoustic_fingerprint,
            duration=song.duration,
        )

        print("✅ Consulta completada")
        print()
        print("Respuesta recibida:")
        print("=" * 55)

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    except AcoustIDClientError as exc:
        print("❌ Error de AcoustID:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()