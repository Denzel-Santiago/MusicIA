from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

from app.application.ports.library import LocalLibraryFiles, SongRepository
from app.domain.metadata.metadata_cleaner import clean_resolved_metadata
from app.domain.metadata.metadata_normalizer import normalize_metadata
from app.domain.metadata.metadata_resolver import resolve_metadata
from app.domain.music.song import SongRecord


class NormalizeLibraryMetadata:
    def __init__(self, repository: SongRepository) -> None:
        self.repository = repository

    def execute(self) -> dict[str, int]:
        songs = self.repository.list_all()
        updated = 0
        for song in songs:
            normalized = normalize_metadata({
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "genre": song.genre,
                "year": song.year,
                "duration": song.duration,
            })
            changed = False
            for field in ("title", "artist", "album", "genre"):
                value = normalized[field]
                if getattr(song, field) != value:
                    setattr(song, field, value)
                    changed = True
            if changed:
                updated += 1
        if updated:
            self.repository.save_all(songs)
        return {"total_songs": len(songs), "updated_songs": updated}


class ResolveLibraryMetadata:
    def __init__(self, repository: SongRepository, files: LocalLibraryFiles) -> None:
        self.repository = repository
        self.files = files

    def execute(self) -> dict[str, Any]:
        songs = self.repository.list_all()
        processed = skipped = updated = 0
        changes = []
        changed_songs = []
        for song in songs:
            file_path = Path(song.file_path)
            if not self.files.file_exists(file_path):
                skipped += 1
                continue
            metadata = normalize_metadata(self.files.read_metadata(file_path))
            resolved = resolve_metadata(metadata, file_path.name)
            old = {
                "normalized_title": song.normalized_title,
                "normalized_artist": song.normalized_artist,
                "metadata_source": song.metadata_source,
                "metadata_confidence": song.metadata_confidence,
            }
            song.normalized_title = resolved.get("title")
            song.normalized_artist = resolved.get("artist")
            song.metadata_source = resolved.get("metadata_source")
            song.metadata_confidence = resolved.get("metadata_confidence")
            new = {
                "normalized_title": song.normalized_title,
                "normalized_artist": song.normalized_artist,
                "metadata_source": song.metadata_source,
                "metadata_confidence": song.metadata_confidence,
            }
            if old != new:
                updated += 1
                changed_songs.append(song)
                changes.append({"file": file_path.name, "old": old, "new": new})
            processed += 1
        if changed_songs:
            self.repository.save_all(changed_songs)
        return {
            "total_songs": len(songs),
            "processed_songs": processed,
            "skipped_songs": skipped,
            "updated_songs": updated,
            "changes": changes,
        }


class PreviewCleanMetadata:
    def __init__(self, repository: SongRepository) -> None:
        self.repository = repository

    def execute(self) -> dict[str, Any]:
        songs = self.repository.list_all()
        changes = []
        for song in songs:
            before = song.normalized_title
            after = clean_resolved_metadata({"title": before})["title"]
            if before != after:
                changes.append({"file": Path(song.file_path).name, "before": before, "after": after})
        return {
            "total_songs": len(songs),
            "songs_with_changes": len(changes),
            "songs_without_changes": len(songs) - len(changes),
            "changes": changes,
        }


class ApplyCleanMetadata:
    def __init__(self, repository: SongRepository) -> None:
        self.repository = repository

    def execute(self) -> dict[str, Any]:
        songs = self.repository.list_all()
        changes = []
        changed_songs: list[SongRecord] = []
        protected_fields = [field.name for field in fields(SongRecord) if field.name != "normalized_title"]
        for song in songs:
            before = song.normalized_title
            after = clean_resolved_metadata({"title": before})["title"]
            if before == after:
                continue
            protected_values = {name: getattr(song, name) for name in protected_fields}
            song.normalized_title = after
            if any(getattr(song, name) != value for name, value in protected_values.items()):
                raise RuntimeError("Protected song metadata changed during cleanup.")
            changed_songs.append(song)
            changes.append({"file": Path(song.file_path).name, "before": before, "after": after})
        if changed_songs:
            self.repository.save_all(changed_songs)
        return {
            "total_songs": len(songs),
            "updated_songs": len(changes),
            "unchanged_songs": len(songs) - len(changes),
            "changes": changes,
        }
