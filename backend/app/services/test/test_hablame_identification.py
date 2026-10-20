from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_identifier import identify_resolved_song


db = SessionLocal()

try:
    song = (
        db.query(Song)
        .filter(Song.id == 1)
        .first()
    )

    if song is None:
        print("No se encontró la canción ID 1.")
        raise SystemExit(1)

    metadata = {
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "genre": song.genre,
        "year": song.year,
        "duration": song.duration,
        "title_source": "metadata",
    }

    filename = song.file_path.split("\\")[-1]

    print("=" * 80)
    print("IDENTIFICACIÓN REAL - ID 1")
    print("=" * 80)

    print("\nDatos originales:")
    print("Título:", repr(song.title))
    print("Artista:", repr(song.artist))
    print("Duración:", repr(song.duration))
    print("Archivo:", repr(filename))

    print("\nConsultando MusicBrainz...")

    result = identify_resolved_song(
        metadata=metadata,
        filename=filename,
    )

    print("\nResultado:")
    print("Título:", result.get("title"))
    print("Artista:", result.get("artist"))
    print("Confianza:", result.get("confidence"))
    print("Fuente:", result.get("source"))
    print("Estado:", result.get("status"))

    print("\nIDs externos:")
    print(result.get("external_ids"))

    print("\nVerificación externa:")
    print(result.get("external_verification"))

    print("\nMatch:")
    print(result.get("match"))

    print("\nCandidatos revisados:")
    print(result.get("candidates_checked"))

    print("\n")
    print("=" * 80)
    print("BASE DE DATOS NO MODIFICADA")
    print("=" * 80)

finally:
    db.close()