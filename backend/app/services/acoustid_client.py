from __future__ import annotations

import requests


ACOUSTID_BASE_URL = "https://api.acoustid.org/v2/lookup"


class AcoustIDClientError(Exception):
    """Error relacionado con la consulta a AcoustID."""


class AcoustIDClient:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise AcoustIDClientError(
                "No se proporcionó una API key de AcoustID."
            )

        self.api_key = api_key
        self.session = requests.Session()

    def lookup(
        self,
        fingerprint: str,
        duration: float,
        meta: str = "recordingids",
    ) -> dict:
        """
        Consulta AcoustID utilizando un fingerprint de Chromaprint.

        La respuesta puede incluir información de MusicBrainz
        asociada al fingerprint.
        """

        if not fingerprint:
            raise AcoustIDClientError(
                "El fingerprint está vacío."
            )

        if duration is None:
            raise AcoustIDClientError(
                "La duración es necesaria para consultar AcoustID."
            )

        payload = {
            "format": "json",
            "client": self.api_key,
            "fingerprint": fingerprint,
            "duration": int(round(duration)),
            "meta": meta,
        }

        try:
            response = self.session.post(
                ACOUSTID_BASE_URL,
                data=payload,
                timeout=20,
            )

            if not response.ok:
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = response.text.strip()

                raise AcoustIDClientError(
                    f"AcoustID respondió HTTP "
                    f"{response.status_code}: "
                    f"{error_data}"
                )

        except requests.RequestException as exc:
            raise AcoustIDClientError(
                f"No se pudo consultar AcoustID: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise AcoustIDClientError(
                "AcoustID devolvió una respuesta "
                "que no es JSON válido."
            ) from exc

        if data.get("status") != "ok":
            error = data.get("error", {})

            if isinstance(error, dict):
                message = error.get(
                    "message",
                    "Error desconocido de AcoustID.",
                )
            else:
                message = str(error)

            raise AcoustIDClientError(
                f"AcoustID rechazó la consulta: {message}"
            )

        return data


def create_acoustid_client(api_key: str) -> AcoustIDClient:
    """
    Crea una instancia del cliente de AcoustID.
    """

    return AcoustIDClient(api_key)