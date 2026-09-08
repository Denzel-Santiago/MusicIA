from pathlib import Path

from sqlalchemy.orm import Session

from app.models.song import Song
from app.services.scanner import calculate_file_hash, read_metadata
from app.services.metadata_normalizer import normalize_metadata
from app.services.metadata_resolver import resolve_metadata


def save_song(db: Session, file_path: Path):
    file_hash = calculate_file_hash(file_path)

    existing_song = (
        db.query(Song)
        .filter(Song.file_hash == file_hash)
        .first()
    )

    if existing_song:
        path_changed = existing_song.file_path != str(file_path)

        if path_changed:
            existing_song.file_path = str(file_path)

        existing_song.is_available = True

        db.commit()
        db.refresh(existing_song)

        return {
            "status": "updated" if path_changed else "unchanged",
            "song": existing_song,
        }

    metadata = read_metadata(file_path)
    metadata = normalize_metadata(metadata)

    resolved_metadata = resolve_metadata(
    metadata,
    file_path.name
)

    song = Song(
        title=metadata.get("title"),
        artist=metadata.get("artist"),
        album=metadata.get("album"),
        genre=metadata.get("genre"),
        year=metadata.get("year"),
        duration=metadata.get("duration"),

        normalized_title=resolved_metadata.get("title"),
        normalized_artist=resolved_metadata.get("artist"),
        metadata_source=resolved_metadata.get("metadata_source"),
        metadata_confidence=resolved_metadata.get("metadata_confidence"),

        file_path=str(file_path),
        file_hash=file_hash,
        is_available=True,
    )

    db.add(song)
    db.commit()
    db.refresh(song)

    return {
        "status": "new",
        "song": song,
    }