"""Cliente para realizar consultas a MusicBrainz."""

from __future__ import annotations

import time
from typing import Any

import requests


MUSICBRAINZ_BASE_URL = "https://musicbrainz.org/ws/2"

USER_AGENT = (
    "MusicAI/0.1.0 "
    "(personal music library project)"
)

# MusicBrainz recomienda no superar 1 solicitud por segundo.
# Dejamos un pequeño margen de seguridad.
MIN_REQUEST_INTERVAL = 1.1


class MusicBrainzClient:

    def __init__(self) -> None:
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
        )

        self._last_request_time = 0.0

    def _wait_for_rate_limit(self) -> None:
        """
        Garantiza un intervalo mínimo entre solicitudes.
        """

        elapsed = (
            time.monotonic()
            - self._last_request_time
        )

        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(
                MIN_REQUEST_INTERVAL - elapsed
            )

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """
        Realiza una solicitud GET a MusicBrainz.

        Los errores 429, 503 y los errores de red se consideran
        temporales y se manejan mediante reintentos con
        exponential backoff.

        Si todos los intentos fallan, devuelve None en lugar
        de lanzar una excepción.

        Esto permite que MusicAI continúe procesando las demás
        canciones aunque MusicBrainz no esté disponible.
        """

        url = f"{MUSICBRAINZ_BASE_URL}/{endpoint}"

        for attempt in range(max_retries + 1):

            self._wait_for_rate_limit()

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=15,
                )

                self._last_request_time = (
                    time.monotonic()
                )

                # -------------------------------------------------
                # 429 = Too Many Requests
                # 503 = Service Temporarily Unavailable
                # -------------------------------------------------

                if response.status_code in (429, 503):

                    if attempt >= max_retries:
                        print(
                            "MusicBrainz no está disponible "
                            "después de varios intentos. "
                            f"HTTP {response.status_code}."
                        )

                        return None

                    wait_time = 2 ** attempt

                    print(
                        "MusicBrainz respondió "
                        f"{response.status_code}. "
                        "Reintentando en "
                        f"{wait_time} segundos..."
                    )

                    time.sleep(wait_time)

                    continue

                # -------------------------------------------------
                # Otros errores HTTP
                # -------------------------------------------------

                response.raise_for_status()

                return response.json()

            except requests.RequestException as exc:

                if attempt >= max_retries:
                    print(
                        "No se pudo consultar MusicBrainz "
                        "después de varios intentos. "
                        f"Error: {type(exc).__name__}"
                    )

                    return None

                wait_time = 2 ** attempt

                print(
                    "Error temporal al consultar "
                    "MusicBrainz. "
                    f"Reintentando en "
                    f"{wait_time} segundos..."
                )

                time.sleep(wait_time)

        # Seguridad adicional.
        return None

    @staticmethod
    def _extract_artists(
        recording: dict[str, Any],
    ) -> list[str]:
        """
        Extrae los nombres de los artistas de un recording
        de MusicBrainz.
        """

        artist_credit = recording.get(
            "artist-credit",
            [],
        )

        artists = []

        for credit in artist_credit:

            artist_data = credit.get(
                "artist",
                {},
            )

            artist_name = artist_data.get(
                "name"
            )

            if artist_name:
                artists.append(
                    artist_name
                )

        return artists

    @classmethod
    def _normalize_recording(
        cls,
        recording: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convierte un recording de MusicBrainz al formato
        interno utilizado por MusicAI.
        """

        duration_ms = recording.get(
            "length"
        )

        duration = None

        if duration_ms is not None:
            duration = duration_ms / 1000.0

        artists = cls._extract_artists(
            recording
        )

        return {
            "mbid": recording.get("id"),

            "title": recording.get("title"),

            "artists": artists,

            "artist": (
                ", ".join(artists)
                if artists
                else None
            ),

            "duration": duration,
        }

    def search_recordings(
        self,
        title: str,
        artist: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Busca grabaciones en MusicBrainz utilizando
        título y, opcionalmente, artista.

        Devuelve resultados ya convertidos al formato
        interno de MusicAI.

        Si MusicBrainz no está disponible o la solicitud
        falla después de los reintentos, devuelve una
        lista vacía.
        """

        if not title:
            return []

        query_parts = [
            f'recording:"{title}"'
        ]

        if artist:
            query_parts.append(
                f'artist:"{artist}"'
            )

        query = " AND ".join(
            query_parts
        )

        data = self._get(
            "recording",
            {
                "query": query,
                "limit": limit,
                "fmt": "json",
            },
        )

        # ---------------------------------------------------------
        # MusicBrainz no respondió correctamente.
        #
        # No lanzamos excepción.
        # El identificador podrá continuar con la siguiente
        # consulta/canción.
        # ---------------------------------------------------------

        if not data:
            return []

        recordings = data.get(
            "recordings",
            [],
        )

        return [
            self._normalize_recording(
                recording
            )
            for recording in recordings
        ]


def create_musicbrainz_client() -> MusicBrainzClient:
    """
    Crea una instancia del cliente MusicBrainz.
    """

    return MusicBrainzClient()


if __name__ == "__main__":

    client = create_musicbrainz_client()

    results = client.search_recordings(
        title="The Nights",
        artist="Avicii",
        limit=5,
    )

    print(
        f"Resultados encontrados: {len(results)}"
    )

    for index, recording in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"Resultado #{index}"
        )

        print(
            f"MBID: "
            f"{recording.get('mbid')}"
        )

        print(
            f"Título: "
            f"{recording.get('title')}"
        )

        print(
            f"Artista: "
            f"{recording.get('artist')}"
        )

        print(
            f"Duración: "
            f"{recording.get('duration')}"
        )