from pathlib import Path
import re
from mutagen import File
import hashlib

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".ogg",
}


def scan_music_folder(folder_path: str):
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(
            f"La carpeta no existe: {folder_path}"
        )

    if not folder.is_dir():
        raise NotADirectoryError(
            f"La ruta no es una carpeta: {folder_path}"
        )

    music_files = []

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        music_files.append(file_path)

    return music_files

def read_metadata(file_path: Path):
    audio = File(file_path, easy=True)

    if audio is None:
        return {
            "title": file_path.stem,
            "artist": None,
            "album": None,
            "genre": None,
            "year": None,
            "duration": None,
            "title_source": "filename_fallback",
        }

    def get_first_value(key):
        value = audio.get(key)

        if value:
            return value[0]

        return None

    title = get_first_value("title")
    artist = get_first_value("artist")
    album = get_first_value("album")
    genre = get_first_value("genre")
    date = get_first_value("date")

    duration = None

    if audio.info and hasattr(audio.info, "length"):
        duration = audio.info.length

    year = None

    if date:
        match = re.search(r"\d{4}", str(date))

        if match:
            year = int(match.group())

    title_source = "metadata"

    if not title:
        title = file_path.stem
        title_source = "filename_fallback"

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "genre": genre,
        "year": year,
        "duration": duration,
        "title_source": title_source,
    }
    
def calculate_file_hash(file_path: Path) -> str:
    """
    Calcula el hash SHA-256 de un archivo.

    Permite identificar archivos que tienen
    exactamente el mismo contenido.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()

def calculate_file_hash(file_path: Path) -> str:
    """
    Calcula el hash SHA-256 de un archivo.

    Permite identificar archivos que tienen
    exactamente el mismo contenido.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()

def find_duplicates(files: list[Path]):
    """
    Detecta archivos duplicados mediante SHA-256.

    Devuelve:
    - unique_files: archivos únicos
    - duplicates: archivos descartados por ser duplicados
    """

    hashes = {}
    unique_files = []
    duplicates = []

    for file_path in files:
        file_hash = calculate_file_hash(file_path)

        if file_hash in hashes:
            duplicates.append({
                "file": file_path,
                "duplicate_of": hashes[file_hash],
                "hash": file_hash,
            })

        else:
            hashes[file_hash] = file_path
            unique_files.append(file_path)

    return unique_files, duplicates