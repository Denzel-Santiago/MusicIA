from pathlib import Path

from sqlalchemy.orm import Session

from app.models.song import Song
from app.services.scanner import calculate_file_hash, read_metadata


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

    song = Song(
        title=metadata.get("title"),
        artist=metadata.get("artist"),
        album=metadata.get("album"),
        genre=metadata.get("genre"),
        year=metadata.get("year"),
        duration=metadata.get("duration"),
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