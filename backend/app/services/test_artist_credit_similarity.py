from app.services.acoustic_identity_comparator import (
    _artist_credit_similarity,
)


TEST_CASES = [
    {
        "name": "Banda MS vs nombre completo",
        "local": "Banda MS",
        "acoustic": "Banda MS de Sergio Lizárraga",
        "expected": 1.0,
    },
    {
        "name": "Avicii vs colaboración",
        "local": "Avicii",
        "acoustic": "Avicii, Billy Raffoul",
        "expected": 1.0,
    },
    {
        "name": "Feat vs crédito separado",
        "local": "Avicii Feat. Sandro Cavazza",
        "acoustic": "Avicii, Sandro Cavazza",
        "expected": 1.0,
    },
    {
        "name": "Artistas idénticos",
        "local": "Avicii",
        "acoustic": "Avicii",
        "expected": 1.0,
    },
    {
        "name": "Artistas diferentes",
        "local": "Avicii",
        "acoustic": "The Beatles",
        "expected": 0.0,
    },
    {
        "name": "Bandas diferentes",
        "local": "Banda MS",
        "acoustic": "Banda El Recodo",
        "expected": 0.0,
    },
]


def main():
    print("MusicAI - prueba de similitud de créditos de artistas")
    print("=" * 65)

    passed = 0
    failed = 0

    for index, case in enumerate(TEST_CASES, start=1):
        similarity = _artist_credit_similarity(
            case["local"],
            case["acoustic"],
        )

        expected = case["expected"]
        success = similarity == expected

        if success:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"

        print(f"\n[{index}/{len(TEST_CASES)}] {case['name']}")
        print(f"  Local:     {case['local']}")
        print(f"  Acústico:  {case['acoustic']}")
        print(f"  Esperado:  {expected}")
        print(f"  Obtenido:  {similarity}")
        print(f"  Resultado: {status}")

    print("\n" + "=" * 65)
    print("Resumen")
    print(f"Pruebas correctas: {passed}")
    print(f"Pruebas fallidas:  {failed}")

    if failed == 0:
        print("\n✅ Todas las pruebas pasaron correctamente.")
    else:
        print("\n❌ Hay pruebas que necesitan revisión.")


if __name__ == "__main__":
    main()