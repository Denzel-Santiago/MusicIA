from __future__ import annotations

from typing import Any, Protocol


class ExternalProviderError(Exception):
    """Error de transporte o respuesta de un proveedor externo."""


class RecordingSearch(Protocol):
    def search_recordings(self, title: str, artist: str | None = None, limit: int = 5) -> list[dict[str, Any]]: ...

    def get_recording(self, recording_id: str) -> dict[str, Any]: ...


class AcousticLookup(Protocol):
    def lookup(self, fingerprint: str, duration: float, meta: str = "recordingids") -> dict[str, Any]: ...


class FingerprintGenerator(Protocol):
    def generate(self, file_path: str) -> dict[str, Any]: ...
