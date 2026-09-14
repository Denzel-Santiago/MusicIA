from __future__ import annotations

import subprocess
from pathlib import Path


class AcousticFingerprintError(Exception):
    """Error relacionado con la generación de fingerprints acústicos."""


def generate_fingerprint(
    file_path: str | Path,
) -> dict[str, str | int | float]:
    """
    Genera una huella acústica usando fpcalc.

    Parameters
    ----------
    file_path:
        Ruta del archivo de audio.

    Returns
    -------
    dict:
        Información de la huella acústica generada.
    """

    path = Path(file_path)

    if not path.exists():
        raise AcousticFingerprintError(
            f"El archivo no existe: {path}"
        )

    if not path.is_file():
        raise AcousticFingerprintError(
            f"La ruta no corresponde a un archivo: {path}"
        )

    try:
        result = subprocess.run(
            [
                "fpcalc",
                "-json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AcousticFingerprintError(
            "No se encontró 'fpcalc'. "
            "Verifica que Chromaprint esté instalado y "
            "agregado al PATH de Windows."
        ) from exc
    except OSError as exc:
        raise AcousticFingerprintError(
            f"No se pudo ejecutar fpcalc: {exc}"
        ) from exc

    if result.returncode != 0:
        error_message = result.stderr.strip()

        raise AcousticFingerprintError(
            "fpcalc no pudo procesar el archivo."
            + (
                f" Detalle: {error_message}"
                if error_message
                else ""
            )
        )

    try:
        import json

        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AcousticFingerprintError(
            "fpcalc devolvió una respuesta que no es JSON válido."
        ) from exc

    fingerprint = data.get("fingerprint")
    duration = data.get("duration")

    if not fingerprint:
        raise AcousticFingerprintError(
            "fpcalc no devolvió una huella acústica."
        )

    return {
        "fingerprint": fingerprint,
        "duration": duration,
    }