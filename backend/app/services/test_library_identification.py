from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_identifier import identify_resolved_song


def get_status_icon(result):
    verification = result["external_verification"]
    quality = result["resolution"]["quality"]

    if quality["status"] == "suspicious":
        return "🔴"

    if verification["needed"] and verification["query_ready"]:
        return "🟡"

    if result["status"] == "resolved":
        return "🟢"

    return "⚪"


def main():
    db = SessionLocal()

    try:
        songs = (
            db.query(Song)
            .filter(Song.is_available.is_(True))
            .order_by(Song.id)
            .all()
        )

        print("=" * 90)
        print("MUSICAI - AUDITOR DE IDENTIFICACIÓN")
        print("=" * 90)
        print(f"Canciones disponibles: {len(songs)}")
        print()

        counters = {
            "green": 0,
            "yellow": 0,
            "red": 0,
            "white": 0,
        }

        external_needed = 0
        external_query_ready = 0

        for song in songs:
            metadata = {
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "genre": song.genre,
                "year": song.year,
                "duration": song.duration,
                "title_source": (
                    "filename_fallback"
                    if song.title == song.file_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1].rsplit(".", 1)[0]
                    else "metadata"
                ),
                "normalized_title": song.normalized_title,
                "normalized_artist": song.normalized_artist,
            }

            filename = song.file_path.rsplit("\\", 1)[-1]
            filename = filename.rsplit("/", 1)[-1]

            result = identify_resolved_song(
                metadata=metadata,
                filename=filename,
            )

            icon = get_status_icon(result)

            verification = result["external_verification"]
            quality = result["resolution"]["quality"]

            if icon == "🟢":
                counters["green"] += 1
            elif icon == "🟡":
                counters["yellow"] += 1
            elif icon == "🔴":
                counters["red"] += 1
            else:
                counters["white"] += 1

            if verification["needed"]:
                external_needed += 1

            if verification["query_ready"]:
                external_query_ready += 1

            print("-" * 90)
            print(f"{icon} ID {song.id}")
            print(f"Archivo: {filename}")
            print(f"Título: {result['title']}")
            print(f"Artista: {result['artist']}")
            print(f"Estado: {result['status']}")
            print(f"Confianza: {result['confidence']}")
            print(f"Fuente: {result['source']}")
            print(
                f"Calidad: {quality['status']} "
                f"({quality['confidence']})"
            )
            print(
                f"Verificación externa: "
                f"needed={verification['needed']} | "
                f"query_ready={verification['query_ready']} | "
                f"reason={verification['reason']}"
            )

        print()
        print("=" * 90)
        print("RESUMEN")
        print("=" * 90)

        print(f"🟢 Identificación local suficiente: {counters['green']}")
        print(f"🟡 Necesitan posible verificación externa: {counters['yellow']}")
        print(f"🔴 Metadata sospechosa: {counters['red']}")
        print(f"⚪ Información insuficiente: {counters['white']}")
        print()
        print(f"Verificación externa necesaria: {external_needed}")
        print(f"Consultas externas posibles: {external_query_ready}")
        print()
        print("IMPORTANTE:")
        print("Este proceso NO modifica SQLite.")
        print("Este proceso NO modifica archivos de música.")
        print("Este proceso NO escribe metadata.")

    finally:
        db.close()


if __name__ == "__main__":
    main()