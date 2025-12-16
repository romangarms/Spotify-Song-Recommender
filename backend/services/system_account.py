"""
System Account Authentication Module

This module handles authentication for the system Spotify account.
The system account is used to create playlists on behalf of users
and to fetch public profile/playlist data.

The system account uses a refresh token stored as an environment variable.
The refresh token is obtained once through an admin OAuth flow and then
used to get fresh access tokens as needed.
"""

import os
import re
import requests
import base64
import threading
import spotipy
from datetime import datetime, timedelta

# Thread-safe cache for the system account access token
_token_lock = threading.Lock()
_token_cache = {
    "access_token": None,
    "expires_at": None,
}


def get_system_spotify():
    """
    Get a Spotipy client authenticated with the system account.
    Uses the refresh token from environment variables.

    Returns:
        spotipy.Spotify: Authenticated Spotify client

    Raises:
        ValueError: If SPOTIFY_SYSTEM_REFRESH_TOKEN is not set
    """
    refresh_token = os.getenv("SPOTIFY_SYSTEM_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError(
            "SPOTIFY_SYSTEM_REFRESH_TOKEN environment variable is not set. "
            "Please visit /api/admin/spotify-setup to configure the system account."
        )

    # Thread-safe token caching
    with _token_lock:
        # Check if we have a valid cached token
        if _token_cache["access_token"] and _token_cache["expires_at"]:
            if datetime.now() < _token_cache["expires_at"]:
                return spotipy.Spotify(auth=_token_cache["access_token"])

        # Get a new access token using the refresh token
        access_token = refresh_access_token(refresh_token)

    return spotipy.Spotify(auth=access_token)


def refresh_access_token(refresh_token):
    """
    Use the refresh token to get a new access token.

    Args:
        refresh_token: The Spotify refresh token

    Returns:
        str: New access token

    Raises:
        Exception: If token refresh fails
    """
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    # Create authorization header
    auth_header = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.text}")

    data = response.json()
    access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)

    # Cache the token with expiry time (with 60 second buffer)
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 60)

    return access_token


def parse_user_id_from_url(profile_url):
    """
    Extract user ID from a Spotify profile URL, URI, or plain username.

    Supports formats:
    - https://open.spotify.com/user/abc123
    - https://open.spotify.com/user/abc123?si=xxx
    - spotify:user:abc123
    - abc123 (plain username)

    Args:
        profile_url: Spotify profile URL, URI, or plain username

    Returns:
        str: User ID or None if invalid
    """
    if not profile_url:
        return None

    profile_url = profile_url.strip()

    # Handle Spotify URI format (include periods in pattern)
    uri_match = re.match(r"spotify:user:([a-zA-Z0-9_.-]+)", profile_url)
    if uri_match:
        return uri_match.group(1)

    # Handle URL format (include periods in pattern)
    url_match = re.match(
        r"https?://open\.spotify\.com/user/([a-zA-Z0-9_.-]+)",
        profile_url
    )
    if url_match:
        return url_match.group(1)

    # Handle plain username (alphanumeric, underscores, hyphens, periods)
    if re.match(r"^[a-zA-Z0-9_.-]+$", profile_url):
        return profile_url

    return None


def parse_playlist_id_from_url(playlist_url):
    """
    Extract playlist ID from a Spotify playlist URL.

    Supports formats:
    - https://open.spotify.com/playlist/xyz123
    - https://open.spotify.com/playlist/xyz123?si=xxx
    - spotify:playlist:xyz123

    Args:
        playlist_url: Spotify playlist URL or URI

    Returns:
        str: Playlist ID or None if invalid
    """
    if not playlist_url:
        return None

    playlist_url = playlist_url.strip()

    # Handle Spotify URI format
    uri_match = re.match(r"spotify:playlist:([a-zA-Z0-9]+)", playlist_url)
    if uri_match:
        return uri_match.group(1)

    # Handle URL format
    url_match = re.match(
        r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)",
        playlist_url
    )
    if url_match:
        return url_match.group(1)

    return None


def get_user_profile(user_id):
    """
    Fetch a user's public profile using the system account.

    Args:
        user_id: Spotify user ID

    Returns:
        dict: User profile data with keys: id, display_name, images, external_urls

    Raises:
        ValueError: If user not found
        Exception: If API error
    """
    sp = get_system_spotify()
    try:
        user = sp.user(user_id)
        return {
            "id": user["id"],
            "display_name": user.get("display_name") or user["id"],
            "images": user.get("images", []),
            "external_urls": user.get("external_urls", {}),
        }
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            raise ValueError(f"User '{user_id}' not found")
        raise


def get_user_public_playlists(user_id):
    """
    Fetch a user's public playlists using the system account.

    Args:
        user_id: Spotify user ID

    Returns:
        list: List of playlist dicts with keys: id, name, images, tracks_total
    """
    sp = get_system_spotify()
    playlists = []

    results = sp.user_playlists(user_id, limit=50)

    while results:
        for item in results["items"]:
            # Only include public playlists
            if item.get("public", False):
                playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "images": item.get("images", []),
                    "tracks_total": item["tracks"]["total"],
                })

        if results["next"]:
            results = sp.next(results)
        else:
            break

    return playlists


def get_playlist_tracks(playlist_id):
    """
    Fetch tracks from a public playlist using the system account.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        dict: Playlist data with name and tracks

    Raises:
        ValueError: If playlist not found or not accessible
    """
    sp = get_system_spotify()

    try:
        playlist = sp.playlist(playlist_id)
        return playlist
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            raise ValueError(
                "Couldn't access this playlist. "
                "Make sure the playlist is public and the link is correct."
            )
        raise


def create_playlist_on_system_account(name, description=""):
    """
    Create a new playlist on the system account.

    Args:
        name: Playlist name
        description: Playlist description

    Returns:
        str: Created playlist ID
    """
    sp = get_system_spotify()
    user_id = sp.me()["id"]

    playlist = sp.user_playlist_create(
        user_id,
        name,
        public=True,  # Must be public so users can access it
        description=description,
    )

    return playlist["id"]
