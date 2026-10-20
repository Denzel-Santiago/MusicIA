from __future__ import annotations

from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_identifier import identify_resolved_song
from app.services.metadata_matcher import rank_candidates


SONG_ID = 32


def main() -> None:
    db = SessionLocal()

    try:
        song = db.query(Song).filter(Song.id == SONG_ID).first()

        if song is None:
            print(f"No se encontró la canción con ID {SONG_ID}.")
            return

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

        print("=" * 90)
        print("DIAGNÓSTICO MUSICBRAINZ - THE NIGHTS")
        print("=" * 90)

        print()
        print("DATOS LOCALES")
        print("-" * 90)
        print(f"ID:        {song.id}")
        print(f"Archivo:   {filename}")
        print(f"Título:    {song.title!r}")
        print(f"Artista:   {song.artist!r}")
        print(f"Duración:  {song.duration}")

        print()
        print("EJECUTANDO IDENTIFICACIÓN...")
        print("-" * 90)

        result = identify_resolved_song(
            metadata=metadata,
            filename=filename,
        )

        print()
        print("RESULTADO DE MUSICAI")
        print("-" * 90)
        print(f"Título final:       {result.get('title')!r}")
        print(f"Artista final:      {result.get('artist')!r}")
        print(f"Confianza:          {result.get('metadata_confidence')}")
        print(f"Fuente:             {result.get('metadata_source')}")
        print(f"Estado:             {result.get('status')}")
        print(f"Identity status:    {result.get('identity_status')}")

        external = result.get("external_verification", {})

        print()
        print("VERIFICACIÓN EXTERNA")
        print("-" * 90)
        print(f"Intentada:          {external.get('attempted')}")
        print(f"Razón:              {external.get('reason')}")
        print(f"Error:              {external.get('error')}")
        print(f"Errores:            {external.get('errors')}")
        print(f"Queries:")
        for query in external.get("queries", []):
            print(f"  - {query}")

        print()
        print("MATCH FINAL")
        print("-" * 90)

        match = result.get("match")

        if not match:
            print("No existe match final.")
        else:
            print(f"Score:               {match.get('score')}")
            print(f"Clasificación:       {match.get('classification')}")
            print(f"Similitud título:    {match.get('title_similarity')}")
            print(f"Similitud artista:   {match.get('artist_similarity')}")
            print(f"Similitud duración:  {match.get('duration_similarity')}")
            print(f"Consulta utilizada:  {match.get('query_title')} / {match.get('query_artist')}")
            print(f"Razón consulta:      {match.get('query_reason')}")
            print(f"MBID:                {match.get('mbid')}")

        print()
        print("CANDIDATOS REVISADOS")
        print("-" * 90)

        candidates = external.get("candidates", [])

        if not candidates:
            print("No hay candidatos disponibles en el resultado.")
        else:
            for index, candidate in enumerate(candidates, start=1):
                print()
                print(f"Candidato #{index}")
                print(f"  MBID:       {candidate.get('mbid')}")
                print(f"  Título:     {candidate.get('title')!r}")
                print(f"  Artista:    {candidate.get('artist')!r}")
                print(f"  Duración:   {candidate.get('duration')}")

        print()
        print("=" * 90)
        print("FIN DEL DIAGNÓSTICO")
        print("=" * 90)
        print()
        print("La base de datos NO fue modificada.")

    finally:
        db.close()


if __name__ == "__main__":
    main()