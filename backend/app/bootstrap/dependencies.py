from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.filesystem.library_files import LocalLibraryFiles
from app.adapters.persistence.sqlalchemy.database import get_db
from app.adapters.persistence.sqlalchemy.song_repository import SQLAlchemySongRepository
from app.application.use_cases.library import ListSongs, ScanLibrary
from app.application.use_cases.metadata import (
    ApplyCleanMetadata,
    NormalizeLibraryMetadata,
    PreviewCleanMetadata,
    ResolveLibraryMetadata,
)


def get_song_repository(
    session: Session = Depends(get_db),
) -> SQLAlchemySongRepository:
    return SQLAlchemySongRepository(session)


def get_scan_library_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> ScanLibrary:
    return ScanLibrary(
        repository=repository,
        files=LocalLibraryFiles(),
    )


def get_list_songs_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> ListSongs:
    return ListSongs(repository)


def get_normalize_library_metadata_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> NormalizeLibraryMetadata:
    return NormalizeLibraryMetadata(repository)


def get_resolve_library_metadata_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> ResolveLibraryMetadata:
    return ResolveLibraryMetadata(repository, LocalLibraryFiles())


def get_preview_clean_metadata_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> PreviewCleanMetadata:
    return PreviewCleanMetadata(repository)


def get_apply_clean_metadata_use_case(
    repository: SQLAlchemySongRepository = Depends(get_song_repository),
) -> ApplyCleanMetadata:
    return ApplyCleanMetadata(repository)
