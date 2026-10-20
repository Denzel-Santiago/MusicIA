from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_identifier import identify_resolved_song


TEST_IDS = [32, 35, 37, 26, 10]


db = SessionLocal()

try:
    songs = (
        db.query(Song)
        .filter(Song.id.in_(TEST_IDS))
        .order_by(Song.id)
        .all()
    )

    print("=" * 90)
    print("PRUEBA DE IDENTIFICACIÓN EXTERNA - 5 CANCIONES")
    print("=" * 90)

    for song in songs:
        print("\n")
        print("-" * 90)
        print(f"ID {song.id}")
        print("-" * 90)

        filename = song.file_path.split("\\")[-1]

        metadata = {
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "genre": song.genre,
            "year": song.year,
            "duration": song.duration,
            "title_source": (
                "filename_fallback"
                if song.artist is None
                else "metadata"
            ),
        }

        print("Archivo:")
        print(filename)

        print("\nMetadata original:")
        print("  Título:", repr(song.title))
        print("  Artista:", repr(song.artist))
        print("  Duración:", repr(song.duration))

        print("\nConsultando MusicBrainz...")

        result = identify_resolved_song(
            metadata=metadata,
            filename=filename,
        )

        print("\nRESULTADO")
        print("  Título:", result.get("title"))
        print("  Artista:", result.get("artist"))
        print("  Confianza:", result.get("confidence"))
        print("  Fuente:", result.get("source"))
        print("  Estado:", result.get("status"))

        print("\nMatch:")
        match = result.get("match")

        if match:
            print("  Score:", match.get("score"))
            print("  Clasificación:", match.get("classification"))
            print(
                "  Similitud título:",
                match.get("title_similarity"),
            )
            print(
                "  Similitud artista:",
                match.get("artist_similarity"),
            )
            print(
                "  Similitud duración:",
                match.get("duration_similarity"),
            )
            print(
                "  Consulta utilizada:",
                match.get("query_title"),
                "/",
                match.get("query_artist"),
            )
            print(
                "  Razón:",
                match.get("query_reason"),
            )
        else:
            print("  No hubo coincidencia.")

        print("\nIDs externos:")
        print(result.get("external_ids"))

        print("\nCandidatos revisados:")
        print(result.get("candidates_checked"))

    print("\n")
    print("=" * 90)
    print("FIN DE LA PRUEBA")
    print("=" * 90)
    print("La base de datos NO fue modificada.")

finally:
    db.close()
