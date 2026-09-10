from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_resolver import resolve_metadata
from app.services.metadata_identifier import identify_song_with_musicbrainz


def main():
    db = SessionLocal()

    try:
        song = (
            db.query(Song)
            .filter(
                Song.is_available.is_(True),
                Song.file_path.like("%Hablame De Ti%")
            )
            .first()
        )

        if song is None:
            print("No se encontró la canción de prueba.")
            return

        print("\n=============================")
        print("PRUEBA CON CANCIÓN REAL")
        print("=============================")

        print("\nDatos originales de SQLite:")
        print(f"ID: {song.id}")
        print(f"Título: {song.title}")
        print(f"Artista: {song.artist}")
        print(f"Álbum: {song.album}")
        print(f"Duración: {song.duration}")
        print(f"Ruta: {song.file_path}")

        metadata = {
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "genre": song.genre,
            "year": song.year,
            "duration": song.duration,
            "normalized_title": song.normalized_title,
            "normalized_artist": song.normalized_artist,
            "title_source": "filename_fallback",
        }

        filename = song.file_path.rsplit("\\", 1)[-1]

        resolved = resolve_metadata(
            metadata,
            filename,
        )

        print("\nMetadata resuelto:")
        print(f"Título: {resolved['title']}")
        print(f"Artista: {resolved['artist']}")
        print(f"Fuente: {resolved['metadata_source']}")
        print(f"Confianza: {resolved['metadata_confidence']}")

        external_metadata = {
            **metadata,
            "title": resolved["title"],
            "artist": resolved["artist"],
        }

        print("\nConsultando MusicBrainz...")

        result = identify_song_with_musicbrainz(
            external_metadata,
            limit=5,
        )

        print("\nResultado de identificación:")
        print(f"Título: {result['title']}")
        print(f"Artista: {result['artist']}")
        print(f"Score: {result['confidence']}")
        print(f"Estado: {result['status']}")
        print(f"Fuente: {result['source']}")

        print(
            "MBID: "
            f"{result['external_ids'].get('musicbrainz_recording')}"
        )

        print(
            f"Candidatos revisados: "
            f"{result.get('candidates_checked')}"
        )

        match = result.get("match", {})

        print("\nDetalles del match:")
        print(
            f"Título: "
            f"{match.get('title_similarity')}"
        )
        print(
            f"Artista: "
            f"{match.get('artist_similarity')}"
        )
        print(
            f"Duración: "
            f"{match.get('duration_similarity')}"
        )

        print("\n=============================")
        print("PRUEBA FINALIZADA")
        print("=============================")

        print(
            "\nLa base de datos NO fue modificada."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()