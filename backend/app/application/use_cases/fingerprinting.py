from __future__ import annotations

from app.application.ports.external_services import FingerprintGenerator
from app.application.ports.library import SongRepository
from app.domain.music.song import SongRecord


class FingerprintStorageError(Exception):
    """No fue posible generar o persistir la huella acústica."""


class GenerateAndStoreFingerprint:
    def __init__(self, repository: SongRepository, generator: FingerprintGenerator) -> None:
        self.repository = repository
        self.generator = generator

    def execute(self, song: SongRecord) -> SongRecord:
        try:
            result = self.generator.generate(song.file_path)
            fingerprint = result.get("fingerprint")
            if not fingerprint:
                raise FingerprintStorageError("El fingerprint generado está vacío.")
            song.acoustic_fingerprint = fingerprint
            return self.repository.save(song)
        except FingerprintStorageError:
            raise
        except Exception as exc:
            raise FingerprintStorageError(
                f"No se pudo generar o guardar el fingerprint para '{song.file_path}': {exc}"
            ) from exc


class FingerprintLibrary:
    def __init__(self, repository: SongRepository, generator: FingerprintGenerator) -> None:
        self.repository = repository
        self.generate_one = GenerateAndStoreFingerprint(repository, generator)

    def execute(self) -> dict[str, int]:
        songs = self.repository.list_available_without_fingerprint()
        processed = errors = 0
        for song in songs:
            try:
                self.generate_one.execute(song)
                processed += 1
            except FingerprintStorageError:
                errors += 1
        return {
            "total": len(songs),
            "processed": processed,
            "skipped": 0,
            "errors": errors,
        }
