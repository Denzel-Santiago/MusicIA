from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.scanner import (
    find_duplicates,
    scan_music_folder,
)


router = APIRouter(
    prefix="/songs",
    tags=["Songs"]
)

@router.post("/scan")
def scan_folder(folder_path: str):
    try:
        files = scan_music_folder(folder_path)

        unique_files, duplicates = find_duplicates(files)

        return {
            "folder": folder_path,
            "total_files": len(files),
            "unique_files": len(unique_files),
            "duplicates": len(duplicates),
            "files": [
                str(file)
                for file in unique_files
            ],
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
            detail=str(error)
        )

    except NotADirectoryError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )