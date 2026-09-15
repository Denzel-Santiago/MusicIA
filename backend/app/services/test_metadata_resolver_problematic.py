from __future__ import annotations

from pathlib import Path

from app.services.metadata_resolver import resolve_metadata


def print_case(
    number: int,
    description: str,
    metadata: dict,
    filename: str,
) -> None:
    print()
    print("=" * 75)
    print(f"[{number}] {description}")
    print("=" * 75)

    print("Metadata original:")
    print(f"  Artista: {metadata.get('artist')}")
    print(f"  Título: {metadata.get('title')}")
    print(f"  Fuente del título: {metadata.get('title_source')}")

    print()
    print("Archivo:")
    print(f"  {filename}")

    result = resolve_metadata(
        metadata=metadata,
        filename=filename,
    )

    print()
    print("Resultado del resolver:")
    print(f"  Artista: {result.get('artist')}")
    print(f"  Título: {result.get('title')}")
    print(f"  Fuente: {result.get('metadata_source')}")
    print(f"  Confianza: {result.get('metadata_confidence')}")
    print(f"  Estado: {result.get('resolution_status')}")

    print()
    print("Calidad detectada:")
    quality = result.get("quality", {})
    print(f"  Estado: {quality.get('status')}")
    print(f"  Confianza: {quality.get('confidence')}")
    print(f"  Ruido: {quality.get('has_noise')}")

    print()
    print("Interpretación desde filename parser:")
    filename_result = result.get("filename", {})
    print(f"  Artista: {filename_result.get('artist')}")
    print(f"  Título: {filename_result.get('title')}")
    print(f"  Confianza: {filename_result.get('confidence')}")


def main() -> None:
    print("MusicAI - prueba aislada del metadata resolver")
    print("=" * 75)

    # ------------------------------------------------------------------
    # CASO 1
    # Metadata sospechosa + filename claramente correcto.
    #
    # Este es el caso problemático real de ID 1.
    # ------------------------------------------------------------------
    print_case(
        number=1,
        description="Metadata sospechosa vs filename correcto",
        metadata={
            "title": "Banda MS (Completa)",
            "artist": "(Letra) Hablame De Ti",
            "album": None,
            "genre": None,
            "year": None,
            "duration": 190.97,
            "title_source": "metadata",
        },
        filename="(Letra) Hablame De Ti - Banda MS (Completa).mp3",
    )

    # ------------------------------------------------------------------
    # CASO 2
    # Metadata completamente correcta.
    #
    # El resolver NO debería cambiarla por el filename.
    # ------------------------------------------------------------------
    print_case(
        number=2,
        description="Metadata correcta",
        metadata={
            "title": "The Nights",
            "artist": "Avicii",
            "album": None,
            "genre": None,
            "year": 2014,
            "duration": 175.72,
            "title_source": "metadata",
        },
        filename="Avicii - The Nights.mp3",
    )

    # ------------------------------------------------------------------
    # CASO 3
    # No existe artista en metadata y el título proviene del filename.
    #
    # El resolver debería utilizar el filename.
    # ------------------------------------------------------------------
    print_case(
        number=3,
        description="Metadata incompleta + filename correcto",
        metadata={
            "title": "Waiting For Love",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 231.99,
            "title_source": "metadata",
        },
        filename="Avicii - Waiting For Love.mp3",
    )

    # ------------------------------------------------------------------
    # CASO 4
    # Metadata incompleta y filename sin estructura artista - título.
    #
    # El resolver debería conservar lo que tenga y marcarlo como parcial.
    # ------------------------------------------------------------------
    print_case(
        number=4,
        description="Metadata incompleta + filename ambiguo",
        metadata={
            "title": "Broken Arrows",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 211.0,
            "title_source": "metadata",
        },
        filename="Broken Arrows.mp3",
    )

    # ------------------------------------------------------------------
    # CASO 5
    # Metadata ausente + filename estructurado.
    #
    # Aquí el filename debería ser la fuente principal.
    # ------------------------------------------------------------------
    print_case(
        number=5,
        description="Sin metadata + filename estructurado",
        metadata={
            "title": "Avicii - Lonely Together",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 181.0,
            "title_source": "filename_fallback",
        },
        filename="Avicii - Lonely Together.mp3",
    )

    # ------------------------------------------------------------------
    # CASO 6
    # Filename invertido problemático.
    #
    # Debe demostrar si el resolver aprovecha correctamente la nueva
    # regla extract_reversed_lyric_filename().
    # ------------------------------------------------------------------
    print_case(
        number=6,
        description="Filename invertido tipo '(Letra) Titulo - Artista (Completa)'",
        metadata={
            "title": "(Letra) Hablame De Ti - Banda MS (Completa)",
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": 190.97,
            "title_source": "filename_fallback",
        },
        filename="(Letra) Hablame De Ti - Banda MS (Completa).mp3",
    )

    # ------------------------------------------------------------------
    # CASO 7
    # Metadata correcta aunque el filename tenga una versión.
    #
    # Queremos comprobar que NO se destruya información musical válida
    # como Remix / Radio Edit / Original Mix.
    # ------------------------------------------------------------------
    print_case(
        number=7,
        description="Metadata correcta + filename con versión musical",
        metadata={
            "title": "Without You (AFISHAL Remix)",
            "artist": "Avicii",
            "album": None,
            "genre": None,
            "year": None,
            "duration": 240.0,
            "title_source": "metadata",
        },
        filename="Avicii - Without You (AFISHAL Remix).mp3",
    )

    print()
    print("=" * 75)
    print("PRUEBA FINALIZADA")
    print("=" * 75)
    print()
    print("Esta prueba NO modifica SQLite.")


if __name__ == "__main__":
    main()