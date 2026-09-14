from pathlib import Path

from app.services.acoustic_fingerprint import (
    generate_fingerprint,
    AcousticFingerprintError,
)


BASE_DIR = Path(__file__).resolve().parents[3]

SONG_PATH = (
    BASE_DIR
    / "music"
    / "(Letra) Hablame De Ti - Banda MS (Completa).mp3"
)


def main() -> None:
    print("MusicAI - prueba de estabilidad del fingerprint")
    print("=" * 55)

    print(f"Archivo: {SONG_PATH}")
    print(f"Existe: {SONG_PATH.exists()}")
    print()

    try:
        print("Generando fingerprint #1...")
        result_1 = generate_fingerprint(SONG_PATH)

        print("Generando fingerprint #2...")
        result_2 = generate_fingerprint(SONG_PATH)

        fingerprint_1 = result_1["fingerprint"]
        fingerprint_2 = result_2["fingerprint"]

        print()
        print("Resultados:")
        print(f"Duración #1: {result_1['duration']} segundos")
        print(f"Duración #2: {result_2['duration']} segundos")
        print()

        print(
            f"Longitud #1: {len(fingerprint_1)} caracteres"
        )
        print(
            f"Longitud #2: {len(fingerprint_2)} caracteres"
        )
        print()

        if fingerprint_1 == fingerprint_2:
            print("✅ FINGERPRINT ESTABLE")
            print("Las dos huellas son idénticas.")
        else:
            print("❌ FINGERPRINT INESTABLE")
            print("Las dos huellas son diferentes.")

    except AcousticFingerprintError as exc:
        print("ERROR:")
        print(exc)


if __name__ == "__main__":
    main()