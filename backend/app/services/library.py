"""Compatibility facade for saving one scanned song."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.adapters.filesystem.library_files import LocalLibraryFiles
from app.adapters.persistence.sqlalchemy.song_repository import SQLAlchemySongRepository
from app.application.use_cases.library import SaveSong


def save_song(db: Session, file_path: Path):
    return SaveSong(
        SQLAlchemySongRepository(db),
        LocalLibraryFiles(),
    ).execute(file_path)
