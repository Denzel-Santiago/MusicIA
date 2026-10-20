from app.services.acoustic_identity_comparator import (
    compare_acoustic_identity,
)


TEST_CASES = [
    {
        "name": "Coincidencia exacta",
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
        "name": "Diferencia singular/plural",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Night",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "conflict",
        "expected_decision": "review_required",
    },
    {
        "name": "Mismo título con Original Mix",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights (Original Mix)",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "review",
        "expected_decision": "review_recommended",
    },
    {
        "name": "Mismo título con Remix",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights Remix",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "review",
        "expected_decision": "review_recommended",
    },
    {
        "name": "Título y artista completamente diferentes",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "Wake Me Up",
            "artist": "Avicii",
            "acoustid_score": 0.98,
        },
        "expected_classification": "conflict",
        "expected_decision": "review_required",
    },
    {
        "name": "Artista completamente diferente",
        "local": {
            "title": "The Nights",
            "artist": "Avicii",
        },
        "acoustic": {
            "status": "identified",
            "title": "The Nights",
            "artist": "The Beatles",
            "acoustid_score": 0.98,
        },
        "expected_classification": "conflict",
        "expected_decision": "review_required",
    },
    {
        "name": "Banda MS abreviada",
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
        "name": "Artistas con colaboración",
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
]


def run_tests():
    passed = 0

    print("\n=== TEST EXTENDIDO DE POLÍTICA ACÚSTICA ===\n")

    for case in TEST_CASES:
        result = compare_acoustic_identity(
            local_metadata=case["local"],
            acoustic_metadata=case["acoustic"],
        )

        classification_ok = (
            result["classification"]
            == case["expected_classification"]
        )

        decision_ok = (
            result["decision"]
            == case["expected_decision"]
        )

        success = classification_ok and decision_ok

        print(case["name"])
        print(f"  Título:     {result['local']['title']}")
        print(f"  Artista:    {result['local']['artist']}")
        print(
            f"  Similitud título: "
            f"{result['title_similarity']}"
        )
        print(
            f"  Similitud artista: "
            f"{result['artist_similarity']}"
        )
        print(
            f"  Clasificación: "
            f"{result['classification']}"
        )
        print(
            f"  Decisión: "
            f"{result['decision']}"
        )

        if success:
            print("  Resultado: PASS\n")
            passed += 1
        else:
            print(
                "  Resultado: FAIL "
                f"(esperado: "
                f"{case['expected_classification']} / "
                f"{case['expected_decision']})\n"
            )

    print("==============================================")
    print(
        f"Resultado final: "
        f"{passed}/{len(TEST_CASES)} casos correctos"
    )
    print("==============================================\n")


if __name__ == "__main__":
    run_tests()