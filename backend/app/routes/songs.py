from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.song import Song
from app.services.scanner import find_duplicates, scan_music_folder
from app.services.library import save_song
from app.services.metadata_normalizer import normalize_metadata
from pathlib import Path
from app.services.scanner import read_metadata
from app.services.metadata_resolver import resolve_metadata

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post("/scan")
def scan_folder(
    folder_path: str,
    db: Session = Depends(get_db),
):
    try:
        files = scan_music_folder(folder_path)

        unique_files, duplicates = find_duplicates(files)

        new_songs = 0
        unchanged_songs = 0
        updated_songs = 0

        scanned_hashes = set()

        for file_path in unique_files:
            result = save_song(db, file_path)

            song = result["song"]
            scanned_hashes.add(song.file_hash)

            if result["status"] == "new":
                new_songs += 1

            elif result["status"] == "unchanged":
                unchanged_songs += 1

            elif result["status"] == "updated":
                updated_songs += 1

        missing_songs = 0

        songs = db.query(Song).all()

        for song in songs:
            if song.file_hash not in scanned_hashes:
                if song.is_available:
                    song.is_available = False
                    missing_songs += 1

        db.commit()

        return {
            "folder": folder_path,
            "total_files": len(files),
            "unique_files": len(unique_files),
            "duplicates": len(duplicates),
            "new_songs": new_songs,
            "unchanged_songs": unchanged_songs,
            "updated_songs": updated_songs,
            "missing_songs": missing_songs,
            "duplicate_files": [
                {
                    "file": str(item["file"]),
                    "duplicate_of": str(item["duplicate_of"]),
                }
                for item in duplicates
            ],
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except NotADirectoryError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get("")
def get_songs(db: Session = Depends(get_db)):
    songs = db.query(Song).all()

    return songs

@router.post("/normalize")
def normalize_library(db: Session = Depends(get_db)):
    songs = db.query(Song).all()

    updated_songs = 0

    for song in songs:

        original_data = {
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "genre": song.genre,
            "year": song.year,
            "duration": song.duration,
        }

        normalized_data = normalize_metadata(original_data)

        changed = False

        if song.title != normalized_data["title"]:
            song.title = normalized_data["title"]
            changed = True

        if song.artist != normalized_data["artist"]:
            song.artist = normalized_data["artist"]
            changed = True

        if song.album != normalized_data["album"]:
            song.album = normalized_data["album"]
            changed = True

        if song.genre != normalized_data["genre"]:
            song.genre = normalized_data["genre"]
            changed = True

        if changed:
            updated_songs += 1

    db.commit()

    return {
        "total_songs": len(songs),
        "updated_songs": updated_songs,
    }
    
@router.post("/resolve-metadata")
def resolve_library_metadata(db: Session = Depends(get_db)):
    songs = db.query(Song).all()

    processed_songs = 0
    skipped_songs = 0
    updated_songs = 0

    changes = []

    for song in songs:

        file_path = Path(song.file_path)

        if not file_path.exists():
            skipped_songs += 1
            continue

        metadata = read_metadata(file_path)
        metadata = normalize_metadata(metadata)

        resolved_metadata = resolve_metadata(
            metadata,
            file_path.name
        )

        old_values = {
            "normalized_title": song.normalized_title,
            "normalized_artist": song.normalized_artist,
            "metadata_source": song.metadata_source,
            "metadata_confidence": song.metadata_confidence,
        }

        song.normalized_title = resolved_metadata.get("title")
        song.normalized_artist = resolved_metadata.get("artist")
        song.metadata_source = resolved_metadata.get("metadata_source")
        song.metadata_confidence = resolved_metadata.get("metadata_confidence")

        new_values = {
            "normalized_title": song.normalized_title,
            "normalized_artist": song.normalized_artist,
            "metadata_source": song.metadata_source,
            "metadata_confidence": song.metadata_confidence,
        }

        if old_values != new_values:
            updated_songs += 1

            changes.append({
                "file": file_path.name,
                "old": old_values,
                "new": new_values,
            })

        processed_songs += 1

    db.commit()

    return {
        "total_songs": len(songs),
        "processed_songs": processed_songs,
        "skipped_songs": skipped_songs,
        "updated_songs": updated_songs,
        "changes": changes,
    }