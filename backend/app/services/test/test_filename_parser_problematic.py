from app.services.filename_parser import (
    extract_artist_title_from_filename,
)


TEST_FILENAMES = [
    "(Letra) Hablame De Ti - Banda MS (Completa).mp3",
    "Avicii - The Nights.mp3",
    "Avicii - Waiting For Love.mp3",
    "Broken Arrows.mp3",
    "Avicii - Without You (AFISHAL Remix).mp3",
    "Artist A - Song Title feat. Artist B.mp3",
    "Song Title - Original Mix.mp3",
]


def main() -> None:
    print("MusicAI - prueba de nombres problemáticos")
    print("=" * 70)

    for index, filename in enumerate(TEST_FILENAMES, start=1):
        result = extract_artist_title_from_filename(filename)

        print(f"[{index}/{len(TEST_FILENAMES)}] {filename}")
        print("-" * 70)
        print(f"  Artista: {result.get('artist')}")
        print(f"  Título: {result.get('title')}")
        print(f"  Confianza: {result.get('confidence')}")
        print()


if __name__ == "__main__":
    main()
