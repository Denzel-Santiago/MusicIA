from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.scanner import find_duplicates, scan_music_folder
from app.services.library import save_song
from app.models.song import Song


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

        for file_path in unique_files:
            result = save_song(db, file_path)

            if result["status"] == "new":
                new_songs += 1
            elif result["status"] == "unchanged":
                unchanged_songs += 1

        return {
            "folder": folder_path,
            "total_files": len(files),
            "unique_files": len(unique_files),
            "duplicates": len(duplicates),
            "new_songs": new_songs,
            "unchanged_songs": unchanged_songs,
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