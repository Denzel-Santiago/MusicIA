"""
MusicAI - Fase 3.1: prueba aislada del diseño del Audio Analyzer.

Ejecutar desde MusicAI/backend:

    python -m app.services.test.test_audio_analyzer_design

- Genera audio sintético en una carpeta temporal (no usa music/).
- NO modifica SQLite.
- Si existe music/ con archivos, además carga UNA canción real.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from app.services.audio_analyzer import (
    ANALYSIS_SAMPLE_RATE,
    FEATURE_NAMES,
    FEATURE_STATUSES,
    AudioLoadError,
    FeatureResult,
    analyze_file,
    load_audio,
)
from app.services.scanner import SUPPORTED_EXTENSIONS


BASE_DIR = Path(__file__).resolve().parents[4]
MUSIC_DIR = BASE_DIR / "music"

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, info: str = "") -> None:
    results.append((name, condition, info))
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ->  {info}" if info else ""))


def make_sine(path: Path, seconds: float, extra_args: list[str] | None = None) -> None:
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-nostdin", "-y",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
            *(extra_args or []),
            str(path),
        ],
        check=True,
    )


def main() -> None:
    print("MusicAI - Fase 3.1: diseño del Audio Analyzer")
    print("=" * 55)

    with tempfile.TemporaryDirectory(prefix="musicai_test_") as tmp:
        tmp_dir = Path(tmp)

        wav = tmp_dir / "sine_5s.wav"
        mp3 = tmp_dir / "sine_5s.mp3"
        corrupt = tmp_dir / "corrupt.mp3"
        missing = tmp_dir / "no_existe.mp3"

        make_sine(wav, 5)
        make_sine(mp3, 5, ["-ar", "44100", "-ac", "2"])
        corrupt.write_bytes(np.random.default_rng(0).bytes(4096))

        print("\n1) Lectura de WAV sintético (5 s)")
        audio = load_audio(wav)
        check("dtype float32", audio.samples.dtype == np.float32)
        check("mono (1 dimensión)", audio.samples.ndim == 1)
        check("sample rate de análisis", audio.sample_rate == ANALYSIS_SAMPLE_RATE,
              str(audio.sample_rate))
        check("duración ~5.0 s", abs(audio.duration - 5.0) < 0.05,
              f"{audio.duration:.3f} s")
        check("señal no silenciosa", float(np.max(np.abs(audio.samples))) > 0.01)

        print("\n2) Lectura de MP3 estéreo 44.1 kHz (se convierte a mono 22.05 kHz)")
        audio_mp3 = load_audio(mp3)
        check("MP3 convertido a mono", audio_mp3.samples.ndim == 1)
        check("MP3 duración ~5.0 s", abs(audio_mp3.duration - 5.0) < 0.1,
              f"{audio_mp3.duration:.3f} s")

        print("\n3) Determinismo")
        again = load_audio(wav)
        check("misma señal en dos lecturas", np.array_equal(audio.samples, again.samples))

        print("\n4) Estructura del reporte")
        report = analyze_file(wav)
        check("status analyzed", report["status"] == "analyzed", report["status"])
        check("todas las características presentes",
              set(report["features"]) == set(FEATURE_NAMES))
        check("cada característica tiene value/confidence/status/method/detail",
              all(set(f) == {"value", "confidence", "status", "method", "detail"}
                  for f in report["features"].values()))
        check("estados válidos",
              all(f["status"] in FEATURE_STATUSES for f in report["features"].values()))
        check("pendientes marcados unavailable/not_implemented",
              all(f["status"] == "unavailable" and f["detail"] == "not_implemented"
                  for f in report["features"].values()))
        check("no inventa confianza",
              all(f["confidence"] is None for f in report["features"].values()))

        print("\n5) Aislamiento de errores entre extractores")

        def broken(_):
            raise RuntimeError("fallo simulado")

        def ok(_):
            return FeatureResult(value=1.0, status="analyzed", method="test")

        report = analyze_file(wav, extractors={"bpm": broken, "key": ok})
        check("extractor roto -> failed", report["features"]["bpm"]["status"] == "failed")
        check("los demás siguen funcionando", report["features"]["key"]["status"] == "analyzed")
        check("error registrado", any(e["stage"] == "bpm" for e in report["errors"]))

        print("\n6) Archivos problemáticos (no deben lanzar excepción)")
        for label, path in (("inexistente", missing), ("corrupto", corrupt)):
            report = analyze_file(path)
            check(f"{label} -> status failed", report["status"] == "failed",
                  report["errors"][0]["error"][:70] if report["errors"] else "")

        try:
            load_audio(missing)
            check("load_audio lanza AudioLoadError", False)
        except AudioLoadError:
            check("load_audio lanza AudioLoadError", True)

        try:
            FeatureResult(status="inventado")
            check("rechaza estados no permitidos", False)
        except ValueError:
            check("rechaza estados no permitidos", True)

    print("\n7) Canción real (opcional)")
    real_files = sorted(
        p for p in MUSIC_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ) if MUSIC_DIR.exists() else []

    if not real_files:
        print("  [SKIP] No hay archivos en music/")
    else:
        song = real_files[0]
        report = analyze_file(song)
        check(f"carga real: {song.name[:45]}", report["status"] == "analyzed",
              f"{report['audio']['analysis_duration'] if report['audio'] else '-'} s, "
              f"{report['timing'].get('load_seconds')} s de carga")

    passed = sum(1 for _, ok_, _ in results if ok_)
    print("\n" + "=" * 55)
    print(f"RESULTADO FINAL: {passed}/{len(results)} PASS")
    print("=" * 55)


if __name__ == "__main__":
    main()
