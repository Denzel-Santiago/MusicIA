from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.library import SongRepository
from app.domain.music.song import SongRecord
from app.adapters.persistence.sqlalchemy.song import Song


class SQLAlchemySongRepository(SongRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_record(model: Song) -> SongRecord:
        return SongRecord(**{
            field: getattr(model, field)
            for field in SongRecord.__dataclass_fields__
        })

    @staticmethod
    def _copy_to_model(record: SongRecord, model: Song) -> None:
        for field in SongRecord.__dataclass_fields__:
            if field != "id":
                setattr(model, field, getattr(record, field))

    def find_by_hash(self, file_hash: str) -> SongRecord | None:
        model = self.session.query(Song).filter(Song.file_hash == file_hash).first()
        return self._to_record(model) if model is not None else None

    def add(self, song: SongRecord) -> SongRecord:
        model = Song()
        self._copy_to_model(song, model)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_record(model)

    def save(self, song: SongRecord) -> SongRecord:
        model = self.session.get(Song, song.id)
        if model is None:
            raise LookupError(f"No existe la canción con id {song.id}.")
        self._copy_to_model(song, model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_record(model)

    def save_all(self, songs: list[SongRecord]) -> None:
        for song in songs:
            model = self.session.get(Song, song.id)
            if model is None:
                raise LookupError(f"No existe la canción con id {song.id}.")
            self._copy_to_model(song, model)
        self.session.commit()

    def list_all(self) -> list[SongRecord]:
        return [self._to_record(row) for row in self.session.query(Song).all()]

    def find_by_id(self, song_id: int) -> SongRecord | None:
        model = self.session.get(Song, song_id)
        return self._to_record(model) if model is not None else None

    def list_available_without_fingerprint(self) -> list[SongRecord]:
        rows = (
            self.session.query(Song)
            .filter(Song.is_available.is_(True), Song.acoustic_fingerprint.is_(None))
            .order_by(Song.id)
            .all()
        )
        return [self._to_record(row) for row in rows]

    def mark_unavailable_except(self, file_hashes: set[str]) -> int:
        missing = 0
        for model in self.session.query(Song).all():
            if model.file_hash not in file_hashes and model.is_available:
                model.is_available = False
                missing += 1
        self.session.commit()
        return missing
