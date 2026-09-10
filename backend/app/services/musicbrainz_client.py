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

        elapsed = time.monotonic() - self._last_request_time

        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(
                MIN_REQUEST_INTERVAL - elapsed
            )

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Realiza una solicitud GET a MusicBrainz.

        Los errores 429 y 503 se consideran temporales
        y se manejan mediante reintentos con exponential backoff.
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

                self._last_request_time = time.monotonic()

                # 429 = Too Many Requests
                # 503 = Service Temporarily Unavailable
                if response.status_code in (429, 503):

                    if attempt >= max_retries:
                        response.raise_for_status()

                    wait_time = 2 ** attempt

                    print(
                        f"MusicBrainz respondió "
                        f"{response.status_code}. "
                        f"Reintentando en "
                        f"{wait_time} segundos..."
                    )

                    time.sleep(wait_time)
                    continue

                # Otros errores HTTP
                response.raise_for_status()

                return response.json()

            except requests.RequestException:

                if attempt >= max_retries:
                    raise

                wait_time = 2 ** attempt

                print(
                    "Error temporal al consultar "
                    "MusicBrainz. "
                    f"Reintentando en "
                    f"{wait_time} segundos..."
                )

                time.sleep(wait_time)

        raise RuntimeError(
            "No se pudo obtener una respuesta "
            "de MusicBrainz."
        )

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
            []
        )

        artists = []

        for credit in artist_credit:
            artist_data = credit.get(
                "artist",
                {}
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

        duration_ms = recording.get("length")

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

        query = " AND ".join(query_parts)

        data = self._get(
            "recording",
            {
                "query": query,
                "limit": limit,
                "fmt": "json",
            },
        )

        recordings = data.get(
            "recordings",
            []
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
        print(f"Resultado #{index}")

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

