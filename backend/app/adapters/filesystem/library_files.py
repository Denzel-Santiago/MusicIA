from pathlib import Path

from app.adapters.filesystem.scanner import (
    calculate_file_hash,
    find_duplicates,
    read_metadata,
    scan_music_folder,
)


class LocalLibraryFiles:
    def scan(self, folder_path: str) -> list[Path]:
        return scan_music_folder(folder_path)

    def find_duplicates(self, files: list[Path]) -> tuple[list[Path], list[dict]]:
        return find_duplicates(files)

    def calculate_hash(self, file_path: Path) -> str:
        return calculate_file_hash(file_path)

    def read_metadata(self, file_path: Path) -> dict:
        return read_metadata(file_path)

    def file_exists(self, file_path: Path) -> bool:
        return file_path.is_file()
