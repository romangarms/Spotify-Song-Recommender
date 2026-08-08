"""
System Account Authentication Module

This module handles authentication for the system Spotify account.

Two auth flows are used:
- Client Credentials (get_public_spotify): all public-data reads. Not
  user-scoped, so it is exempt from Spotify's 6-month refresh token expiry.
- Authorization Code refresh token (get_system_spotify): playlist creation
  on the system account only. The refresh token is obtained through the
  admin OAuth flow and expires 6 months after authorization (Spotify policy
  effective July 2026), after which an admin must re-authorize.
"""

import os
import re
import json
import requests
import base64
import threading
import spotipy
from datetime import datetime, timedelta

TOKEN_METADATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "token_metadata.json",
)
TOKEN_LIFETIME_DAYS = 180
TOKEN_WARNING_DAYS = 150


class SystemTokenExpiredError(Exception):
    """The system account refresh token was revoked or hit Spotify's 6-month
    expiry. Recovery requires an admin re-authorizing via /api/admin/spotify-setup."""


# Thread-safe cache for the system account access token
_token_lock = threading.Lock()
_token_cache = {
    "access_token": None,
    "expires_at": None,
}
# Spotify requires discarding an expired refresh token rather than retrying it,
# so once a refresh fails with invalid_grant we fail fast until restart.
_refresh_token_dead = False

_cc_lock = threading.Lock()
_cc_cache = {
    "access_token": None,
    "expires_at": None,
}


def get_public_spotify():
    """
    Get a Spotipy client for public-data reads via the Client Credentials flow.

    Returns:
        spotipy.Spotify: Authenticated Spotify client

    Raises:
        ValueError: If SPOTIPY_CLIENT_ID/SPOTIPY_CLIENT_SECRET are not set
    """
    with _cc_lock:
        if _cc_cache["access_token"] and _cc_cache["expires_at"]:
            if datetime.now() < _cc_cache["expires_at"]:
                return spotipy.Spotify(auth=_cc_cache["access_token"])

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment "
                "variables must be set."
            )

        print("[PublicSpotify] Fetching client credentials token...")
        auth_header = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to get client credentials token: {response.text}"
            )

        data = response.json()
        expires_in = data.get("expires_in", 3600)
        _cc_cache["access_token"] = data["access_token"]
        _cc_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 60)

        return spotipy.Spotify(auth=_cc_cache["access_token"])


def get_system_spotify():
    """
    Get a Spotipy client authenticated with the system account.
    Only needed for writes (playlist creation); reads should use
    get_public_spotify().

    Returns:
        spotipy.Spotify: Authenticated Spotify client

    Raises:
        ValueError: If SPOTIFY_SYSTEM_REFRESH_TOKEN is not set
        SystemTokenExpiredError: If the refresh token is expired or revoked
    """
    refresh_token = os.getenv("SPOTIFY_SYSTEM_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError(
            "SPOTIFY_SYSTEM_REFRESH_TOKEN environment variable is not set. "
            "Please visit /api/admin/spotify-setup to configure the system account."
        )

    if _refresh_token_dead:
        raise SystemTokenExpiredError(
            "System account refresh token is expired or revoked. "
            "Re-authorize at /api/admin/spotify-setup, update "
            "SPOTIFY_SYSTEM_REFRESH_TOKEN, and restart the backend."
        )

    # Thread-safe token caching
    with _token_lock:
        # Check if we have a valid cached token
        if _token_cache["access_token"] and _token_cache["expires_at"]:
            if datetime.now() < _token_cache["expires_at"]:
                print("[SystemAccount] Using cached access token")
                return spotipy.Spotify(auth=_token_cache["access_token"])

        # Get a new access token using the refresh token
        print("[SystemAccount] Refreshing access token...")
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
        SystemTokenExpiredError: If the refresh token is expired or revoked
        Exception: If token refresh fails for any other reason
    """
    global _refresh_token_dead
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    # Debug logging
    print(f"[TokenRefresh] Client ID set: {bool(client_id)}")
    if client_id:
        print(f"[TokenRefresh] Client ID length: {len(client_id)}, starts with: {client_id[:8]}...")
    print(f"[TokenRefresh] Client Secret set: {bool(client_secret)}")
    if client_secret:
        print(f"[TokenRefresh] Client Secret length: {len(client_secret)}")
    print(f"[TokenRefresh] Refresh token length: {len(refresh_token)}, starts with: {refresh_token[:10]}...")

    # Create authorization header
    auth_header = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    print(f"[TokenRefresh] Making request to Spotify token endpoint...")

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

    print(f"[TokenRefresh] Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"[TokenRefresh] Error response: {response.text}")
        if "invalid_grant" in response.text:
            _token_cache["access_token"] = None
            _token_cache["expires_at"] = None
            _refresh_token_dead = True
            raise SystemTokenExpiredError(
                "System account refresh token is expired or revoked. "
                "Re-authorize at /api/admin/spotify-setup, update "
                "SPOTIFY_SYSTEM_REFRESH_TOKEN, and restart the backend."
            )
        raise Exception(f"Failed to refresh token: {response.text}")

    data = response.json()
    access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    print(f"[TokenRefresh] Success! Token expires in {expires_in} seconds")

    # Cache the token with expiry time (with 60 second buffer)
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 60)

    _warn_if_token_expiring()

    return access_token


def record_token_issued():
    """Record when the system refresh token was authorized. Spotify's 6-month
    expiry runs from this moment and is not extended by refreshing."""
    with open(TOKEN_METADATA_FILE, "w") as f:
        json.dump({"issued_at": datetime.now().isoformat()}, f)


def get_token_status():
    """
    Report the system refresh token's age against Spotify's 6-month expiry.

    Returns:
        dict: status is one of "ok", "expiring_soon", "expired", "unknown";
              known ages also include issued_at, expires_at, days_remaining
    """
    if _refresh_token_dead:
        return {
            "status": "expired",
            "message": "Spotify rejected the refresh token (invalid_grant). "
                       "Re-authorize at /api/admin/spotify-setup.",
        }

    if not os.path.exists(TOKEN_METADATA_FILE):
        return {
            "status": "unknown",
            "message": "No token issue date recorded. It will be recorded "
                       "the next time the admin OAuth flow completes.",
        }

    with open(TOKEN_METADATA_FILE) as f:
        issued_at = datetime.fromisoformat(json.load(f)["issued_at"])

    expires_at = issued_at + timedelta(days=TOKEN_LIFETIME_DAYS)
    days_remaining = (expires_at - datetime.now()).days

    if days_remaining < 0:
        status = "expired"
    elif issued_at + timedelta(days=TOKEN_WARNING_DAYS) < datetime.now():
        status = "expiring_soon"
    else:
        status = "ok"

    return {
        "status": status,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "days_remaining": days_remaining,
    }


def _warn_if_token_expiring():
    token_status = get_token_status()
    if token_status["status"] in ("expiring_soon", "expired"):
        print(
            f"[TokenRefresh] WARNING: system refresh token status is "
            f"'{token_status['status']}' "
            f"({token_status.get('days_remaining', '?')} days remaining). "
            f"Re-authorize at /api/admin/spotify-setup before it expires."
        )


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
    Fetch a user's public profile.

    Args:
        user_id: Spotify user ID

    Returns:
        dict: User profile data with keys: id, display_name, images, external_urls

    Raises:
        ValueError: If user not found
        Exception: If API error
    """
    sp = get_public_spotify()
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
    Fetch a user's public playlists.

    Args:
        user_id: Spotify user ID

    Returns:
        list: List of playlist dicts with keys: id, name, images, tracks_total
    """
    sp = get_public_spotify()
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
    Fetch tracks from a public playlist.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        dict: Playlist data with name and tracks

    Raises:
        ValueError: If playlist not found or not accessible
    """
    sp = get_public_spotify()

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
