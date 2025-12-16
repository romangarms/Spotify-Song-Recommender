"""Service modules for Spotify and Logic API integration."""

from .system_account import (
    get_system_spotify,
    parse_user_id_from_url,
    parse_playlist_id_from_url,
    get_user_profile,
    get_user_public_playlists,
    get_playlist_tracks,
    create_playlist_on_system_account,
)
from .spotify import add_recommendations_to_playlist, search_and_get_tracks
from .logic_api import analyze_playlist, generate_from_text
