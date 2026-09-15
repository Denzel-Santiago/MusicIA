from app.services.acoustic_identity_comparator import (
    compare_acoustic_identity,
)


TEST_CASES = [
    {
        "name": "Identidad completamente confirmada",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "confirmed",
        "expected_decision": "identity_confirmed",
    },
    {
        "name": "Artista abreviado compatible",
        "local": {
            "title": "Hablame De Ti",
            "artist": "Banda MS",
        },
        "acoustic": {
            "status": "identified",
            "title": "Háblame de ti",
            "artist": "Banda MS de Sergio Lizárraga",
            "acoustid_score": 0.98,
        },
        "expected_classification": "confirmed",
        "expected_decision": "identity_confirmed",
    },
    {
        "name": "Artista local sin colaborador adicional",
        "local": {
            "title": "You Be Love",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "You Be Love",
            "artist": "Avicii, Billy Raffoul",
            "acoustid_score": 0.96,
        },
        "expected_classification": "confirmed",
        "expected_decision": "identity_confirmed",
    },
    {
        "name": "Créditos equivalentes con formato diferente",
        "local": {
            "title": "Without You",
            "artist": "Avicii Feat. Sandro Cavazza",
        },
        "acoustic": {
            "status": "identified",
            "title": "Without You",
            "artist": "Avicii, Sandro Cavazza",
            "acoustid_score": 0.99,
        },
        "expected_classification": "confirmed",
        "expected_decision": "identity_confirmed",
    },
    {
        "name": "Coincidencia probable",
        "local": {
            "title": "Dreaming of Me",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "Dreaming of Me",
            "artist": "Avicii",
            "acoustid_score": 0.85,
        },
        "expected_classification": "confirmed",
        "expected_decision": "identity_confirmed",
    },
    {
        "name": "Conflicto fuerte",
        "local": {
            "title": "Wake Me Up",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights",
            "artist": "The Beatles",
            "acoustid_score": 0.98,
        },
        "expected_classification": "conflict",
        "expected_decision": "strong_acoustic_conflict",
    },
    {
        "name": "Conflicto con fingerprint de confianza alta",
        "local": {
            "title": "Wake Me Up",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "conflict",
        "expected_decision": "review_required",
    },
    {
        "name": "Coincidencia parcial para revisión",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Night",
            "artist": "Avicii",
            "acoustid_score": 0.70,
        },
        "expected_classification": "review",
        "expected_decision": "review_recommended",
    },
    {
        "name": "Sin identidad acústica",
        "local": {
            "title": "Unknown Song",
            "artist": "Unknown Artist",
        },
        "acoustic": {
            "status": "not_found",
            "title": None,
            "artist": None,
            "acoustid_score": None,
        },
        "expected_classification": "no_acoustic_identity",
        "expected_decision": "no_action",
    },
    {
        "name": "MusicBrainz no disponible",
        "local": {
            "title": "Unknown Song",
            "artist": "Unknown Artist",
        },
        "acoustic": {
            "status": "musicbrainz_lookup_failed",
            "title": None,
            "artist": None,
            "acoustid_score": 0.95,
        },
        "expected_classification": "no_acoustic_identity",
        "expected_decision": "no_action",
    },
]


def main():
    print("MusicAI - prueba de política de decisiones acústicas")
    print("=" * 70)

    passed = 0
    failed = 0

    for index, case in enumerate(TEST_CASES, start=1):
        result = compare_acoustic_identity(
            local_metadata=case["local"],
            acoustic_metadata=case["acoustic"],
        )

        classification = result["classification"]
        decision = result["decision"]

        classification_ok = (
            classification
            == case["expected_classification"]
        )

        decision_ok = (
            decision
            == case["expected_decision"]
        )

        success = classification_ok and decision_ok

        if success:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"

        print(f"\n[{index}/{len(TEST_CASES)}] {case['name']}")
        print(
            f"  Clasificación esperada: "
            f"{case['expected_classification']}"
        )
        print(
            f"  Clasificación obtenida: "
            f"{classification}"
        )
        print(
            f"  Decisión esperada:      "
            f"{case['expected_decision']}"
        )
        print(
            f"  Decisión obtenida:      "
            f"{decision}"
        )
        print(
            f"  Similitud título:       "
            f"{result['title_similarity']}"
        )
        print(
            f"  Similitud artista:      "
            f"{result['artist_similarity']}"
        )
        print(
            f"  Similitud general:      "
            f"{result['overall_similarity']}"
        )
        print(
            f"  AcoustID:               "
            f"{result['acoustic_score']}"
        )
        print(f"  Resultado:              {status}")

    print("\n" + "=" * 70)
    print("Resumen")
    print(f"Pruebas correctas: {passed}")
    print(f"Pruebas fallidas:  {failed}")

    if failed == 0:
        print("\n✅ Todas las pruebas pasaron correctamente.")
    else:
        print("\n❌ Hay pruebas que necesitan revisión.")


if __name__ == "__main__":
    main()