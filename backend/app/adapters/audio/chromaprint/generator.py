from app.adapters.audio.chromaprint.fingerprint import generate_fingerprint


class ChromaprintGenerator:
    def generate(self, file_path: str) -> dict:
        return generate_fingerprint(file_path)
