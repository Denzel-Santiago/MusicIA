from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_quality import evaluate_metadata_quality


def main():
    db = SessionLocal()

    try:
        songs = (
            db.query(Song)
            .filter(Song.is_available.is_(True))
            .order_by(Song.id)
            .limit(10)
            .all()
        )

        print("\n=============================")
        print("PRUEBA DE CALIDAD REAL")
        print("=============================")

        for song in songs:
            filename = song.file_path.rsplit("\\", 1)[-1]

            metadata = {
                "title": song.title,
                "artist": song.artist,
            }

            result = evaluate_metadata_quality(
                metadata,
                filename,
            )

            print("\n-----------------------------")
            print(f"ID: {song.id}")
            print(f"Archivo: {filename}")
            print(f"Título metadata: {song.title}")
            print(f"Artista metadata: {song.artist}")
            print(f"Estado: {result['status']}")
            print(f"Confianza: {result['confidence']}")

            print("Razones:")

            for reason in result["reasons"]:
                print(f"  - {reason}")

        print("\n=============================")
        print("PRUEBA FINALIZADA")
        print("=============================")
        print("\nLa base de datos NO fue modificada.")

    finally:
        db.close()


if __name__ == "__main__":
    main()