from fastapi import APIRouter, Depends, HTTPException

from app.application.use_cases.library import ListSongs, ScanLibrary
from app.application.use_cases.metadata import (
    ApplyCleanMetadata,
    NormalizeLibraryMetadata,
    PreviewCleanMetadata,
    ResolveLibraryMetadata,
)
from app.bootstrap.dependencies import (
    get_apply_clean_metadata_use_case,
    get_list_songs_use_case,
    get_normalize_library_metadata_use_case,
    get_preview_clean_metadata_use_case,
    get_resolve_library_metadata_use_case,
    get_scan_library_use_case,
)

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post("/scan")
def scan_folder(
    folder_path: str,
    use_case: ScanLibrary = Depends(get_scan_library_use_case),
):
    try:
        return use_case.execute(folder_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("")
def get_songs(
    use_case: ListSongs = Depends(get_list_songs_use_case),
):
    return use_case.execute()


@router.post("/normalize")
def normalize_library(
    use_case: NormalizeLibraryMetadata = Depends(get_normalize_library_metadata_use_case),
):
    return use_case.execute()


@router.post("/resolve-metadata")
def resolve_library_metadata(
    use_case: ResolveLibraryMetadata = Depends(get_resolve_library_metadata_use_case),
):
    return use_case.execute()


@router.post("/clean-metadata")
def preview_clean_metadata(
    use_case: PreviewCleanMetadata = Depends(get_preview_clean_metadata_use_case),
):
    return use_case.execute()


@router.post("/clean-metadata/apply")
def apply_clean_metadata(
    use_case: ApplyCleanMetadata = Depends(get_apply_clean_metadata_use_case),
):
    return use_case.execute()
