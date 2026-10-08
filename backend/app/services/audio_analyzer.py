"""
MusicAI - Fase 3.1: Audio Analyzer (diseño base).

Responde a la pregunta: "¿Cómo suena esta canción?"

Este módulo NO toca SQLite, NO modifica archivos de audio y NO decide
qué canción reproducir. Solo lee un archivo y devuelve características
estructuradas.

Capas (separadas a propósito):

    1. Lectura       -> load_audio(): decodifica con FFmpeg a PCM mono float32.
    2. Procesamiento -> LoadedAudio: señal en memoria, misma para todos.
    3. Extracción    -> EXTRACTORS: una función por característica.
    4. Validación    -> FeatureResult + estados controlados.
    5. Almacenamiento-> NO existe aquí. Se diseñará en 3.13 / 3.14.

Cada característica devuelve un FeatureResult:

    value       -> valor medido (o None)
    confidence  -> solo si la herramienta la proporciona; nunca inventada
    status      -> analyzed | uncertain | unavailable | failed
    method      -> cómo se obtuvo (herramienta / algoritmo)
    detail      -> explicación corta cuando no hay valor o hay dudas

Los extractores de 3.2 en adelante se irán registrando en EXTRACTORS
bloque por bloque. Mientras no estén implementados devuelven
status="unavailable" con detail="not_implemented".
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np


ANALYZER_VERSION = "0.1.0"

# Frecuencia de análisis. 22050 Hz es el estándar de facto para análisis
# musical (tempo, key, espectro) y reduce memoria a la mitad frente a 44.1 kHz.
# La frecuencia ORIGINAL del archivo se reportará en 3.2 (información básica).
ANALYSIS_SAMPLE_RATE = 22050

FEATURE_STATUSES = (
    "analyzed",
    "uncertain",
    "unavailable",
    "failed",
)

# Orden en que se reportan las características.
FEATURE_NAMES = (
    "bpm",
    "beats",
    "key",
    "energy",
    "loudness",
    "danceability",
    "spectral",
    "structure",
    "intro",
    "outro",
)


# ============================================================
# Errores
# ============================================================

class AudioAnalyzerError(Exception):
    """Error general del analizador de audio."""


class AudioLoadError(AudioAnalyzerError):
    """El archivo no pudo leerse o decodificarse."""


# ============================================================
# Estructuras
# ============================================================

@dataclass
class FeatureResult:
    value: Any = None
    confidence: float | None = None
    status: str = "unavailable"
    method: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in FEATURE_STATUSES:
            raise ValueError(
                f"Estado de característica inválido: {self.status}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LoadedAudio:
    path: Path
    samples: np.ndarray = field(repr=False)
    sample_rate: int
    duration: float


Extractor = Callable[[LoadedAudio], FeatureResult]


# ============================================================
# 1. Lectura
# ============================================================

def load_audio(
    file_path: str | Path,
    sample_rate: int = ANALYSIS_SAMPLE_RATE,
) -> LoadedAudio:
    """
    Decodifica cualquier formato soportado por FFmpeg a PCM mono
    float32 en memoria. No escribe ningún archivo.

    Se usa FFmpeg porque ya es dependencia del proyecto (fingerprinting)
    y decodifica MP3/FLAC/WAV/M4A/OGG de forma consistente.
    """

    path = Path(file_path)

    if not path.exists():
        raise AudioLoadError(f"El archivo no existe: {path}")

    if not path.is_file():
        raise AudioLoadError(f"La ruta no corresponde a un archivo: {path}")

    command = [
        "ffmpeg",
        "-v", "error",
        "-nostdin",
        "-i", str(path),
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-ac", "1",
        "-ar", str(sample_rate),
        "-",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AudioLoadError(
            "No se encontró 'ffmpeg'. Verifica que esté instalado "
            "y agregado al PATH de Windows."
        ) from exc
    except OSError as exc:
        raise AudioLoadError(f"No se pudo ejecutar ffmpeg: {exc}") from exc

    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise AudioLoadError(
            "FFmpeg no pudo decodificar el archivo."
            + (f" Detalle: {message[-500:]}" if message else "")
        )

    samples = np.frombuffer(result.stdout, dtype=np.float32)

    if samples.size == 0:
        raise AudioLoadError(
            "El archivo se decodificó pero no contiene muestras de audio."
        )

    if not np.all(np.isfinite(samples)):
        raise AudioLoadError(
            "La señal decodificada contiene valores no válidos (NaN/Inf)."
        )

    return LoadedAudio(
        path=path,
        samples=samples,
        sample_rate=sample_rate,
        duration=samples.size / sample_rate,
    )


# ============================================================
# 3. Extracción (registro de extractores)
# ============================================================

def _not_implemented(_: LoadedAudio) -> FeatureResult:
    return FeatureResult(status="unavailable", detail="not_implemented")


# Cada bloque de la Fase 3 reemplazará su entrada aquí cuando esté validado.
EXTRACTORS: dict[str, Extractor] = {
    name: _not_implemented for name in FEATURE_NAMES
}


# ============================================================
# Orquestación
# ============================================================

def analyze_file(
    file_path: str | Path,
    extractors: dict[str, Extractor] | None = None,
) -> dict[str, Any]:
    """
    Analiza un archivo y devuelve un diccionario estructurado.

    Nunca lanza excepción por un archivo problemático: devuelve
    status="failed" con el error, para que el procesamiento de la
    biblioteca pueda continuar con la siguiente canción.
    """

    extractors = EXTRACTORS if extractors is None else extractors
    started = time.perf_counter()

    report: dict[str, Any] = {
        "file": str(file_path),
        "analyzer_version": ANALYZER_VERSION,
        "status": "failed",
        "audio": None,
        "features": {},
        "errors": [],
        "timing": {},
    }

    # 1. Lectura
    try:
        load_started = time.perf_counter()
        audio = load_audio(file_path)
        report["timing"]["load_seconds"] = round(
            time.perf_counter() - load_started, 3
        )
    except AudioLoadError as exc:
        report["errors"].append({"stage": "load", "error": str(exc)})
        report["features"] = {
            name: FeatureResult(status="failed", detail="load_failed").to_dict()
            for name in FEATURE_NAMES
        }
        report["timing"]["total_seconds"] = round(
            time.perf_counter() - started, 3
        )
        return report

    report["audio"] = {
        "analysis_sample_rate": audio.sample_rate,
        "analysis_duration": round(audio.duration, 3),
        "samples": int(audio.samples.size),
    }

    # 3 y 4. Extracción + validación, aisladas por característica.
    for name in FEATURE_NAMES:
        extractor = extractors.get(name, _not_implemented)
        feature_started = time.perf_counter()

        try:
            result = extractor(audio)

            if not isinstance(result, FeatureResult):
                raise AudioAnalyzerError(
                    f"El extractor '{name}' no devolvió un FeatureResult."
                )

        except Exception as exc:  # un extractor no debe tumbar a los demás
            result = FeatureResult(
                status="failed",
                detail=f"{type(exc).__name__}: {exc}",
            )
            report["errors"].append({"stage": name, "error": result.detail})

        report["features"][name] = result.to_dict()
        report["timing"][f"{name}_seconds"] = round(
            time.perf_counter() - feature_started, 3
        )

    report["status"] = "analyzed"
    report["timing"]["total_seconds"] = round(
        time.perf_counter() - started, 3
    )

    return report
