from pathlib import Path

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
        }

    def get_first(tag_name):
        value = audio.get(tag_name)

        if value:
            return value[0]

        return None

    year = get_first("date")

    if year:
        try:
            year = int(str(year)[:4])
        except ValueError:
            year = None

    duration = None

    if audio.info:
        duration = audio.info.length

    return {
        "title": get_first("title") or file_path.stem,
        "artist": get_first("artist"),
        "album": get_first("album"),
        "genre": get_first("genre"),
        "year": year,
        "duration": duration,
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