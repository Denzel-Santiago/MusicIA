from app.database.connection import SessionLocal
from app.models.song import Song
from app.services.metadata_resolver import resolve_metadata
from app.services.metadata_identifier import _build_external_query_candidates


db = SessionLocal()

try:
    songs = (
        db.query(Song)
        .filter(Song.is_available.is_(True))
        .order_by(Song.id)
        .all()
    )

    print("=" * 90)
    print("AUDITORÍA DE IDENTIFICABILIDAD - MUSICAI")
    print("=" * 90)
    print(f"\nCanciones analizadas: {len(songs)}\n")

    summary = {
        "green": 0,
        "yellow": 0,
        "orange": 0,
        "red": 0,
    }

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
                if song.artist is None
                else "metadata"
            ),
        }

        filename = song.file_path.split("\\")[-1]

        resolved = resolve_metadata(
            metadata,
            filename,
        )

        title = resolved.get("title")
        artist = resolved.get("artist")
        resolution_status = resolved.get(
            "resolution_status"
        )

        quality = resolved.get("quality", {})
        quality_status = quality.get("status")

        candidates = _build_external_query_candidates(
            resolved,
            filename,
        )

        # --------------------------------------------------
        # Clasificación
        # --------------------------------------------------

        if (
            resolution_status == "resolved"
            and quality_status != "suspicious"
        ):
            category = "green"
            label = "🟢 IDENTIFICABLE"

        elif candidates:
            category = "yellow"
            label = "🟡 REQUIERE VERIFICACIÓN"

        elif (
            title
            or artist
            or song.duration
        ):
            category = "orange"
            label = "🟠 REQUIERE FINGERPRINTING"

        else:
            category = "red"
            label = "🔴 SIN INFORMACIÓN SUFICIENTE"

        summary[category] += 1

        print("-" * 90)
        print(
            f"ID {song.id:>2} | {label}"
        )
        print(
            f"Archivo: {filename}"
        )
        print(
            f"Título resuelto: {title}"
        )
        print(
            f"Artista resuelto: {artist}"
        )
        print(
            f"Resolución: {resolution_status}"
        )
        print(
            f"Calidad: {quality_status}"
        )
        print(
            f"Candidatos externos: {len(candidates)}"
        )

        if candidates:
            for candidate in candidates:
                print(
                    f"  → {candidate['title']} / "
                    f"{candidate['artist']} "
                    f"[{candidate['reason']}]"
                )

    print("\n")
    print("=" * 90)
    print("RESUMEN")
    print("=" * 90)

    print(
        f"🟢 Identificables:              {summary['green']}"
    )
    print(
        f"🟡 Requieren verificación:     {summary['yellow']}"
    )
    print(
        f"🟠 Requieren fingerprinting:   {summary['orange']}"
    )
    print(
        f"🔴 Sin información suficiente: {summary['red']}"
    )

    print(
        f"\nTotal: {sum(summary.values())}"
    )

    print("\n")
    print(
        "IMPORTANTE: esta auditoría NO modifica SQLite "
        "ni ningún archivo de música."
    )

finally:
    db.close()