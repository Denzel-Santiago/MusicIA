from __future__ import annotations

from typing import Any

from app.services.acoustid_client import (
    AcoustIDClient,
    AcoustIDClientError,
)


class AcousticIdentifierError(Exception):
    """Error relacionado con la identificación acústica."""


def identify_by_fingerprint(
    client: AcoustIDClient,
    fingerprint: str,
    duration: float,
) -> dict[str, Any]:
    """
    Identifica una canción mediante su fingerprint acústico.

    Consulta AcoustID y devuelve los AcoustID encontrados,
    sus puntuaciones y los MusicBrainz Recording IDs asociados.
    """

    if not fingerprint:
        raise AcousticIdentifierError(
            "No se proporcionó un fingerprint acústico."
        )

    if duration is None:
        raise AcousticIdentifierError(
            "La duración es necesaria para la identificación acústica."
        )

    try:
        response = client.lookup(
            fingerprint=fingerprint,
            duration=duration,
            meta="recordingids",
        )

    except AcoustIDClientError as exc:
        raise AcousticIdentifierError(
            "No se pudo identificar la canción mediante "
            f"AcoustID: {exc}"
        ) from exc

    results = response.get("results", [])

    if not results:
        return {
            "status": "not_found",
            "acoustid": None,
            "score": None,
            "musicbrainz_recording_ids": [],
        }

    best_result = max(
        results,
        key=lambda result: result.get("score", 0.0),
    )

    acoustid = best_result.get("id")
    score = best_result.get("score")

    recordings = best_result.get(
        "recordings",
        [],
    )

    musicbrainz_recording_ids = []

    for recording in recordings:
        recording_id = recording.get("id")

        if recording_id:
            musicbrainz_recording_ids.append(
                recording_id
            )

    return {
        "status": "identified",
        "acoustid": acoustid,
        "score": score,
        "musicbrainz_recording_ids": (
            musicbrainz_recording_ids
        ),
    }


def get_acoustic_candidates(
    client: AcoustIDClient,
    fingerprint: str,
    duration: float,
) -> list[dict[str, Any]]:
    """
    Obtiene todos los candidatos devueltos por AcoustID.

    Cada candidato contiene:

    - AcoustID
    - score acústico
    - MusicBrainz Recording ID

    Esta función no selecciona ni descarta candidatos.
    """

    if not fingerprint:
        raise AcousticIdentifierError(
            "No se proporcionó un fingerprint acústico."
        )

    if duration is None:
        raise AcousticIdentifierError(
            "La duración es necesaria para la identificación acústica."
        )

    try:
        response = client.lookup(
            fingerprint=fingerprint,
            duration=duration,
            meta="recordingids",
        )

    except AcoustIDClientError as exc:
        raise AcousticIdentifierError(
            f"No se pudo consultar AcoustID: {exc}"
        ) from exc

    results = response.get(
        "results",
        [],
    )

    candidates = []

    for result in results:
        acoustid = result.get("id")
        score = result.get("score")

        recordings = result.get(
            "recordings",
            [],
        )

        for recording in recordings:
            recording_id = recording.get("id")

            if not recording_id:
                continue

            candidates.append(
                {
                    "acoustid": acoustid,
                    "acoustid_score": score,
                    "musicbrainz_recording_id": (
                        recording_id
                    ),
                }
            )

    return candidates


def rank_acoustic_candidates(
    client: AcoustIDClient,
    musicbrainz_client,
    local_metadata: dict[str, Any],
    fingerprint: str,
    duration: float,
) -> list[dict[str, Any]]:
    """
    Obtiene, enriquece y ordena los candidatos acústicos.

    La puntuación final combina:

    - similitud del título
    - similitud del artista
    - similitud de duración
    - score acústico de AcoustID

    La metadata textual tiene mayor peso que el
    score acústico porque un mismo fingerprint
    puede devolver múltiples recordings.

    No modifica SQLite.
    """

    from app.services.metadata_matcher import (
        calculate_match_score,
    )

    candidates = get_acoustic_candidates(
        client=client,
        fingerprint=fingerprint,
        duration=duration,
    )

    enriched_candidates = []

    processed_mbids = set()

    for candidate in candidates:
        recording_id = candidate.get(
            "musicbrainz_recording_id"
        )

        if not recording_id:
            continue

        # El mismo MBID puede aparecer asociado
        # a más de un AcoustID.
        if recording_id in processed_mbids:
            continue

        processed_mbids.add(recording_id)

        try:
            recording = (
                musicbrainz_client.get_recording(
                    recording_id
                )
            )

        except Exception as exc:
            enriched_candidates.append(
                {
                    "musicbrainz_recording_id": (
                        recording_id
                    ),
                    "acoustid": candidate.get(
                        "acoustid"
                    ),
                    "acoustid_score": candidate.get(
                        "acoustid_score"
                    ),
                    "title": None,
                    "artist": None,
                    "duration": None,
                    "title_similarity": None,
                    "artist_similarity": None,
                    "duration_similarity": None,
                    "metadata_score": None,
                    "final_score": None,
                    "status": "musicbrainz_unavailable",
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            )

            continue

        if not recording:
            enriched_candidates.append(
                {
                    "musicbrainz_recording_id": (
                        recording_id
                    ),
                    "acoustid": candidate.get(
                        "acoustid"
                    ),
                    "acoustid_score": candidate.get(
                        "acoustid_score"
                    ),
                    "title": None,
                    "artist": None,
                    "duration": None,
                    "title_similarity": None,
                    "artist_similarity": None,
                    "duration_similarity": None,
                    "metadata_score": None,
                    "final_score": None,
                    "status": "musicbrainz_unavailable",
                    "error": (
                        "MusicBrainz no devolvió "
                        "información."
                    ),
                }
            )

            continue

        candidate_metadata = {
            "title": recording.get("title"),
            "artist": recording.get("artist"),
            "duration": recording.get("duration"),
        }

        match = calculate_match_score(
            local_metadata=local_metadata,
            candidate=candidate_metadata,
        )

        acoustic_score = candidate.get(
            "acoustid_score"
        )

        if acoustic_score is None:
            acoustic_score = 0.0

        metadata_score = match["score"]

        # La metadata textual tiene mayor peso porque
        # AcoustID puede asociar varios recordings a
        # una misma huella.
        final_score = (
            metadata_score * 0.80
            + acoustic_score * 0.20
        )

        enriched_candidates.append(
            {
                "musicbrainz_recording_id": (
                    recording_id
                ),
                "acoustid": candidate.get(
                    "acoustid"
                ),
                "acoustid_score": acoustic_score,
                "title": recording.get(
                    "title"
                ),
                "artist": recording.get(
                    "artist"
                ),
                "duration": recording.get(
                    "duration"
                ),
                "title_similarity": match[
                    "title_similarity"
                ],
                "artist_similarity": match[
                    "artist_similarity"
                ],
                "duration_similarity": match[
                    "duration_similarity"
                ],
                "metadata_score": metadata_score,
                "final_score": round(
                    final_score,
                    4,
                ),
                "status": "analyzed",
                "error": None,
            }
        )

    enriched_candidates.sort(
        key=lambda candidate: (
            candidate.get("final_score") is not None,
            candidate.get("final_score") or 0.0,
        ),
        reverse=True,
    )

    return enriched_candidates