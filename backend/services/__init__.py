"""Service modules for Spotify and Logic API integration."""

from .system_account import (
    get_system_spotify,
    get_public_spotify,
    SystemTokenExpiredError,
    SYSTEM_ACCOUNT_SCOPES,
    SEARCH_MAX_LIMIT,
    MAX_PASTED_TRACKS,
    parse_track_ids_from_text,
    get_tracks_by_ids,
    create_playlist_on_system_account,
    discard_playlist,
    record_token_issued,
    get_token_status,
)
from .spotify import add_recommendations_to_playlist, search_and_get_tracks
from .logic_api import generate_from_text, recommend_from_tracks
