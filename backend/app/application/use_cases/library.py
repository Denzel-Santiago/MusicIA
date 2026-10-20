from __future__ import annotations

from pathlib import Path
from typing import Any

from app.application.ports.library import LocalLibraryFiles, SongRepository
from app.domain.metadata.metadata_cleaner import clean_resolved_metadata
from app.domain.metadata.metadata_normalizer import normalize_metadata
from app.domain.metadata.metadata_resolver import resolve_metadata
from app.domain.music.song import SongRecord


class SaveSong:
    def __init__(self, repository: SongRepository, files: LocalLibraryFiles) -> None:
        self.repository = repository
        self.files = files

    def execute(self, file_path: Path) -> dict[str, Any]:
        file_hash = self.files.calculate_hash(file_path)
        existing = self.repository.find_by_hash(file_hash)

        if existing is not None:
            path_changed = existing.file_path != str(file_path)
            was_available = existing.is_available
            existing.file_path = str(file_path)
            existing.is_available = True
            if path_changed or not was_available:
                existing = self.repository.save(existing)
            return {
                "status": "updated" if path_changed else "unchanged",
                "song": existing,
            }

        metadata = normalize_metadata(self.files.read_metadata(file_path))
        resolved = resolve_metadata(metadata, file_path.name)
        resolved = clean_resolved_metadata(resolved)
        song = SongRecord(
            title=metadata.get("title"),
            artist=metadata.get("artist"),
            album=metadata.get("album"),
            genre=metadata.get("genre"),
            year=metadata.get("year"),
            duration=metadata.get("duration"),
            normalized_title=resolved.get("title"),
            normalized_artist=resolved.get("artist"),
            metadata_source=resolved.get("metadata_source"),
            metadata_confidence=resolved.get("metadata_confidence"),
            file_path=str(file_path),
            file_hash=file_hash,
            is_available=True,
        )
        return {"status": "new", "song": self.repository.add(song)}


class ScanLibrary:
    def __init__(self, repository: SongRepository, files: LocalLibraryFiles) -> None:
        self.repository = repository
        self.files = files
        self.save_song = SaveSong(repository, files)

    def execute(self, folder_path: str) -> dict[str, Any]:
        files = self.files.scan(folder_path)
        unique_files, duplicates = self.files.find_duplicates(files)
        new_songs = unchanged_songs = updated_songs = 0
        scanned_hashes: set[str] = set()

        for file_path in unique_files:
            result = self.save_song.execute(file_path)
            scanned_hashes.add(result["song"].file_hash)
            if result["status"] == "new":
                new_songs += 1
            elif result["status"] == "unchanged":
                unchanged_songs += 1
            else:
                updated_songs += 1

        missing_songs = self.repository.mark_unavailable_except(scanned_hashes)
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
                {"file": str(item["file"]), "duplicate_of": str(item["duplicate_of"])}
                for item in duplicates
            ],
        }


class ListSongs:
    def __init__(self, repository: SongRepository) -> None:
        self.repository = repository

    def execute(self) -> list[SongRecord]:
        return self.repository.list_all()
