from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.song import Song
from app.services.scanner import find_duplicates, scan_music_folder
from app.services.library import save_song


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