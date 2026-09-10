from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_for_comparison(value: str | None) -> str:
    """
    Normaliza texto únicamente para realizar comparaciones.

    No modifica la metadata original.
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    # Eliminar acentos.
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    # Normalizar separadores y espacios.
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_artist_for_comparison(
    value: str | None,
) -> str:
    """
    Normaliza créditos de artistas para comparación.

    Trata como equivalentes algunas variantes comunes:

        feat.
        ft.
        featuring
        &
        ,
        ;
        +
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    # Unificar variantes de "featuring".
    value = re.sub(
        r"\b(featuring|feat\.?|ft\.?)\b",
        " feat ",
        value,
    )

    # Separadores habituales entre artistas.
    value = re.sub(
        r"\s*(?:&|\+|,|;)\s*",
        " feat ",
        value,
    )

    # Eliminar puntuación restante.
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def calculate_text_similarity(
    value_a: str | None,
    value_b: str | None,
) -> float:
    """
    Calcula una similitud sencilla entre dos textos.

    Devuelve un valor entre 0.0 y 1.0.
    """

    normalized_a = normalize_for_comparison(
        value_a
    )

    normalized_b = normalize_for_comparison(
        value_b
    )

    if not normalized_a or not normalized_b:
        return 0.0

    if normalized_a == normalized_b:
        return 1.0

    tokens_a = set(normalized_a.split())
    tokens_b = set(normalized_b.split())

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


def calculate_duration_similarity(
    local_duration: float | None,
    external_duration: float | None,
) -> float | None:
    """
    Compara la duración de la canción local con la externa.

    Devuelve:

        0.0 - 1.0 si ambas duraciones existen.
        None si alguna de las dos no está disponible.

    Se permite una pequeña diferencia de duración porque
    diferentes archivos o versiones pueden contener algunos
    segundos adicionales o faltantes.
    """

    if (
        local_duration is None
        or external_duration is None
    ):
        return None

    difference = abs(
        local_duration - external_duration
    )

    if difference <= 1:
        return 1.0

    if difference <= 3:
        return 0.95

    if difference <= 5:
        return 0.80

    if difference <= 10:
        return 0.40

    return 0.0


def classify_match_score(
    score: float,
) -> str:
    """
    Clasifica la confianza de una coincidencia.

    Niveles:

        >= 0.95 → confirmed
        >= 0.80 → probable
        >= 0.60 → review
        <  0.60 → rejected
    """

    if score >= 0.95:
        return "confirmed"

    if score >= 0.80:
        return "probable"

    if score >= 0.60:
        return "review"

    return "rejected"


def calculate_match_score(
    local_metadata: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """
    Calcula qué tan probable es que un candidato externo
    corresponda a la canción local.

    Los pesos representan la importancia de cada característica:

        título    = 50%
        artista   = 35%
        duración  = 15%

    Si una característica no está disponible, no se inventa
    información ni se redistribuye su peso.
    """

    title_similarity = calculate_text_similarity(
        local_metadata.get("title"),
        candidate.get("title"),
    )

    artist_similarity = calculate_text_similarity(
        normalize_artist_for_comparison(
            local_metadata.get("artist")
        ),
        normalize_artist_for_comparison(
            candidate.get("artist")
        ),
    )

    duration_similarity = calculate_duration_similarity(
        local_metadata.get("duration"),
        candidate.get("duration"),
    )

    # Pesos de cada característica.
    title_weight = 0.50
    artist_weight = 0.35
    duration_weight = 0.15

    score = (
        title_similarity * title_weight
        + artist_similarity * artist_weight
    )

    if duration_similarity is not None:
        score += (
            duration_similarity
            * duration_weight
        )

    score = round(score, 4)

    return {
        "score": score,
        "classification": classify_match_score(
            score
        ),
        "title_similarity": round(
            title_similarity,
            4,
        ),
        "artist_similarity": round(
            artist_similarity,
            4,
        ),
        "duration_similarity": (
            round(
                duration_similarity,
                4,
            )
            if duration_similarity is not None
            else None
        ),
        "candidate": candidate,
    }


def rank_candidates(
    local_metadata: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Ordena candidatos de mayor a menor coincidencia.
    """

    matches = [
        calculate_match_score(
            local_metadata,
            candidate,
        )
        for candidate in candidates
    ]

    matches.sort(
        key=lambda match: match["score"],
        reverse=True,
    )

    return matches


if __name__ == "__main__":

    local_song = {
        "title": "The Nights",
        "artist": "Avicii",
        "duration": 198.16,
    }

    candidates = [
        {
            "mbid": "candidate-1",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 198.16,
        },
        {
            "mbid": "candidate-2",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": None,
        },
        {
            "mbid": "candidate-3",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 177.0,
        },
        {
            "mbid": "candidate-4",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 173.292,
        },
        {
            "mbid": "candidate-5",
            "title": "The Nights",
            "artist": "Avicii",
            "duration": 246.973,
        },
    ]

    # ---------------------------------------------------------
    # Pruebas de artistas
    # ---------------------------------------------------------

    artist_tests = [
        (
            "Avicii Feat. Sandro Cavazza",
            "Avicii ft. Sandro Cavazza",
        ),
        (
            "Avicii feat. Sandro Cavazza",
            "Avicii Featuring Sandro Cavazza",
        ),
        (
            "Avicii & Sandro Cavazza",
            "Avicii, Sandro Cavazza",
        ),
        (
            "Avicii",
            "Avicii",
        ),
        (
            "Avicii",
            "Alan Walker",
        ),
    ]

    print("\nPruebas de artistas:")

    for artist_a, artist_b in artist_tests:

        similarity = calculate_text_similarity(
            normalize_artist_for_comparison(
                artist_a
            ),
            normalize_artist_for_comparison(
                artist_b
            ),
        )

        print(
            f"{artist_a} <-> {artist_b}"
        )

        print(
            f"Normalizado: "
            f"{normalize_artist_for_comparison(artist_a)}"
            " | "
            f"{normalize_artist_for_comparison(artist_b)}"
        )

        print(
            f"Similitud: {similarity}"
        )

        print()

    # ---------------------------------------------------------
    # Prueba de candidatos
    # ---------------------------------------------------------

    results = rank_candidates(
        local_song,
        candidates,
    )

    print(
        "Coincidencias ordenadas:"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        candidate = result["candidate"]

        print()

        print(
            f"#{index} "
            f"{candidate.get('title')} "
            f"- "
            f"{candidate.get('artist')}"
        )

        print(
            f"MBID: "
            f"{candidate.get('mbid')}"
        )

        print(
            f"Score: "
            f"{result['score']}"
        )

        print(
            f"Clasificación: "
            f"{result['classification']}"
        )

        print(
            f"Título: "
            f"{result['title_similarity']}"
        )

        print(
            f"Artista: "
            f"{result['artist_similarity']}"
        )

        print(
            f"Duración: "
            f"{result['duration_similarity']}"
        )