from __future__ import annotations

import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.persistence.sqlalchemy.database import Base
from app.adapters.persistence.sqlalchemy.song_repository import SQLAlchemySongRepository
from app.application.use_cases.fingerprinting import GenerateAndStoreFingerprint
from app.application.use_cases.library import ScanLibrary


class FakeLibraryFiles:
    def __init__(self, path: Path) -> None:
        self.path = path

    def scan(self, folder_path: str) -> list[Path]:
        return [self.path]

    def find_duplicates(self, files: list[Path]) -> tuple[list[Path], list[dict]]:
        return files, []

    def calculate_hash(self, file_path: Path) -> str:
        return "a" * 64

    def read_metadata(self, file_path: Path) -> dict:
        return {
            "title": "The Nights",
            "artist": "Avicii",
            "album": "True",
            "genre": "Dance",
            "year": 2013,
            "duration": 176.0,
            "title_source": "metadata",
        }

    def file_exists(self, file_path: Path) -> bool:
        return True


class FakeFingerprintGenerator:
    def generate(self, file_path: str) -> dict:
        return {"fingerprint": "sample-fingerprint", "duration": 176}


class ApplicationUseCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.repository = SQLAlchemySongRepository(self.session)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_scan_adds_then_updates_existing_song_without_duplication(self) -> None:
        files = FakeLibraryFiles(Path("Avicii - The Nights.mp3"))
        scan = ScanLibrary(self.repository, files)

        first = scan.execute("virtual-music-folder")
        second = scan.execute("virtual-music-folder")

        self.assertEqual(first["new_songs"], 1)
        self.assertEqual(second["unchanged_songs"], 1)
        self.assertEqual(len(self.repository.list_all()), 1)
        song = self.repository.list_all()[0]
        self.assertEqual(song.normalized_artist, "Avicii")
        self.assertEqual(song.normalized_title, "The Nights")

    def test_fingerprint_use_case_persists_through_repository(self) -> None:
        files = FakeLibraryFiles(Path("Avicii - The Nights.mp3"))
        scan = ScanLibrary(self.repository, files)
        scan.execute("virtual-music-folder")
        song = self.repository.list_all()[0]

        saved = GenerateAndStoreFingerprint(
            self.repository,
            FakeFingerprintGenerator(),
        ).execute(song)

        self.assertEqual(saved.acoustic_fingerprint, "sample-fingerprint")
        self.assertEqual(self.repository.find_by_id(saved.id).acoustic_fingerprint, "sample-fingerprint")


if __name__ == "__main__":
    unittest.main()
