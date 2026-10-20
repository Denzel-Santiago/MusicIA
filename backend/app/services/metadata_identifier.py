"""Compatibility facade; use case lives in app.application.use_cases.identification."""

from app.application.use_cases.identification import *  # noqa: F401,F403
from app.application.use_cases.identification import _build_external_query_candidates  # noqa: F401
from app.adapters.external_services.musicbrainz.client import create_musicbrainz_client
from app.application.use_cases.identification import identify_resolved_song as _identify_resolved_song
from app.application.use_cases.identification import identify_song_with_musicbrainz as _identify_song_with_musicbrainz


def identify_resolved_song(metadata, filename, client=None, limit=5):
    return _identify_resolved_song(metadata, filename, client or create_musicbrainz_client(), limit)


def identify_song_with_musicbrainz(metadata, client=None, limit=5):
    return _identify_song_with_musicbrainz(metadata, client or create_musicbrainz_client(), limit)
