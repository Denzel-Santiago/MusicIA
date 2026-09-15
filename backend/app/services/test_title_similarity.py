from app.services.metadata_matcher import calculate_text_similarity


TEST_CASES = [
    {
        "name": "The Nights vs The Night",
        "local": "The Nights",
        "external": "The Night",
        "expected_min": 0.30,
    },
    {
        "name": "The Nights vs The Nights",
        "local": "The Nights",
        "external": "The Nights",
        "expected_min": 1.00,
    },
    {
        "name": "Hablame De Ti vs Háblame de ti",
        "local": "Hablame De Ti",
        "external": "Háblame de ti",
        "expected_min": 1.00,
    },
    {
        "name": "Waiting For Love vs Waiting for Love",
        "local": "Waiting For Love",
        "external": "Waiting for Love",
        "expected_min": 1.00,
    },
    {
        "name": "The Nights vs Wake Me Up",
        "local": "The Nights",
        "external": "Wake Me Up",
        "expected_max": 0.20,
    },
]


def run_tests():
    passed = 0

    print("\n=== TEST DE SIMILITUD DE TÍTULOS ===\n")

    for case in TEST_CASES:
        score = calculate_text_similarity(
            case["local"],
            case["external"],
        )

        print(f"{case['name']}")
        print(f"  Local:    {case['local']}")
        print(f"  Externo:  {case['external']}")
        print(f"  Score:    {score}")

        expected_min = case.get("expected_min")
        expected_max = case.get("expected_max")

        if expected_min is not None:
            success = score >= expected_min
        elif expected_max is not None:
            success = score <= expected_max
        else:
            success = False

        if success:
            print("  Resultado: PASS\n")
            passed += 1
        else:
            print("  Resultado: FAIL\n")

    print("===================================")
    print(f"Resultado final: {passed}/{len(TEST_CASES)} casos correctos")
    print("===================================\n")


if __name__ == "__main__":
    run_tests()