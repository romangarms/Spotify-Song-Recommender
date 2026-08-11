"""
System Account Authentication Module

This module handles authentication for the system Spotify account.

Two auth flows are used:
- Client Credentials (get_public_spotify): track search and track lookup. Not
  user-scoped, so it is exempt from Spotify's 6-month refresh token expiry.
- Authorization Code refresh token (get_system_spotify): playlist creation and
  every other write. This token expires 6 months after authorization (Spotify
  policy effective July 2026), after which an admin must re-authorize via
  /api/admin/spotify-setup.

Since the February 2026 API changes, no token this app can hold reads other
users' profiles or the items of playlists the system account does not own, so
seed songs come from search and pasted track links instead.
"""

import os
import re
import json
import requests
import base64
import threading
import spotipy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

TOKEN_METADATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "token_metadata.json",
)
TOKEN_LIFETIME_DAYS = 180
TOKEN_WARNING_DAYS = 150

SYSTEM_ACCOUNT_SCOPES = (
    "playlist-modify-public playlist-modify-private "
    "playlist-read-private playlist-read-collaborative user-read-private"
)

# Spotify capped search results at 10 per request in February 2026.
SEARCH_MAX_LIMIT = 10
MAX_PASTED_TRACKS = 100
# Spotify removed batch track fetching in February 2026, so a paste costs one
# request per track, each a ~100ms round trip. They go out concurrently so the
# wait tracks the slowest request rather than their sum.
LOOKUP_WORKERS = 8

RATE_LIMITED_MESSAGE = (
    "Spotify is rate limiting this app right now. Please try again later."
)

TOKEN_EXPIRED_MESSAGE = (
    "System account refresh token is unusable (expired, revoked, or issued "
    "to a different Spotify app). Re-authorize at /api/admin/spotify-setup, "
    "update SPOTIFY_SYSTEM_REFRESH_TOKEN, and restart the backend."
)


class SpotifyRateLimitedError(Exception):
    """Spotify returned 429. Development mode has a daily quota whose
    Retry-After can be many hours, so this fails the request immediately
    rather than waiting it out."""


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

_thread_local = threading.local()


def build_client(access_token):
    """
    Build a Spotipy client that fails fast on 429.

    Spotipy retries 429s by sleeping for Retry-After, which in development
    mode can be most of a day — that turns a rate limit into a hung request,
    so automatic retrying is disabled here.

    Args:
        access_token: Spotify access token

    Returns:
        spotipy.Spotify: Configured client
    """
    return spotipy.Spotify(auth=access_token, retries=0)


def get_public_spotify():
    """
    Get a Spotipy client for public-data reads via the Client Credentials flow.

    Returns:
        spotipy.Spotify: Authenticated Spotify client

    Raises:
        ValueError: If SPOTIPY_CLIENT_ID/SPOTIPY_CLIENT_SECRET are not set
    """
    return build_client(get_public_access_token())


def get_public_access_token():
    """
    Get a valid client credentials access token, refreshing it if expired.

    Returns:
        str: Access token

    Raises:
        ValueError: If SPOTIPY_CLIENT_ID/SPOTIPY_CLIENT_SECRET are not set
    """
    with _cc_lock:
        if _cc_cache["access_token"] and _cc_cache["expires_at"]:
            if datetime.now() < _cc_cache["expires_at"]:
                return _cc_cache["access_token"]

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

        return _cc_cache["access_token"]


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
        raise SystemTokenExpiredError(TOKEN_EXPIRED_MESSAGE)

    # Thread-safe token caching
    with _token_lock:
        # Check if we have a valid cached token
        if _token_cache["access_token"] and _token_cache["expires_at"]:
            if datetime.now() < _token_cache["expires_at"]:
                print("[SystemAccount] Using cached access token")
                return build_client(_token_cache["access_token"])

        # Get a new access token using the refresh token
        print("[SystemAccount] Refreshing access token...")
        access_token = refresh_access_token(refresh_token)

    return build_client(access_token)


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
        # invalid_client here means the token was issued to a different app,
        # not bad credentials: the client credentials flow shares them.
        if "invalid_grant" in response.text or "invalid_client" in response.text:
            _token_cache["access_token"] = None
            _token_cache["expires_at"] = None
            _refresh_token_dead = True
            raise SystemTokenExpiredError(TOKEN_EXPIRED_MESSAGE)
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


def parse_track_ids_from_text(text):
    """
    Extract Spotify track IDs from pasted text.

    Accepts open.spotify.com links, spotify:track: URIs, and bare IDs mixed
    freely and separated by any whitespace, commas, or semicolons — the
    desktop app's "copy link" on a multi-selection yields one URL per line.

    Args:
        text: Pasted text possibly containing many track references

    Returns:
        list: Track IDs, deduplicated, in the order they appear
    """
    if not text:
        return []

    ids = []
    seen = set()

    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue

        match = (
            re.match(r"^https?://open\.spotify\.com/(?:intl-[a-z-]+/)?track/([a-zA-Z0-9]{22})", token)
            or re.match(r"^spotify:track:([a-zA-Z0-9]{22})$", token)
            or re.match(r"^([a-zA-Z0-9]{22})$", token)
        )
        if not match:
            continue

        track_id = match.group(1)
        if track_id not in seen:
            seen.add(track_id)
            ids.append(track_id)

    return ids


def worker_spotify():
    """A Spotify client per worker thread, since a requests Session is not
    safe to share across threads. Rebuilt when the access token rotates."""
    token = get_public_access_token()
    if getattr(_thread_local, "token", None) != token:
        _thread_local.client = build_client(token)
        _thread_local.token = token
    return _thread_local.client


def parallel_map(fn, items):
    """
    Run fn over items concurrently, preserving order.

    Args:
        fn: Callable taking one item
        items: Sequence of items

    Returns:
        list: Results in the same order as items
    """
    if not items:
        return []

    with ThreadPoolExecutor(max_workers=min(LOOKUP_WORKERS, len(items))) as pool:
        return list(pool.map(fn, items))


def fetch_track(track_id):
    """
    Look up one track.

    Args:
        track_id: Spotify track ID

    Returns:
        dict: Track details, or None if Spotify has no such track

    Raises:
        spotipy.exceptions.SpotifyException: On any non-404 Spotify error
    """
    try:
        track = worker_spotify().track(track_id)
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return None
        if e.http_status == 429:
            raise SpotifyRateLimitedError(RATE_LIMITED_MESSAGE)
        raise

    album = track.get("album") or {}
    return {
        "id": track["id"],
        "name": track["name"],
        "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown",
        "album": album.get("name", "Unknown"),
        "release_date": album.get("release_date", ""),
        "image": album["images"][0]["url"] if album.get("images") else None,
    }


def get_tracks_by_ids(track_ids):
    """
    Resolve track IDs to track details, preserving the given order.

    Args:
        track_ids: List of Spotify track IDs

    Returns:
        tuple: (found_tracks, not_found_ids)
    """
    if not track_ids:
        return [], []

    def resolve(track_id):
        try:
            return fetch_track(track_id)
        except spotipy.exceptions.SpotifyException as e:
            print(f"[Tracks] Lookup failed for {track_id}: {e}")
            return None

    resolved = parallel_map(resolve, track_ids)
    found = [t for t in resolved if t]
    not_found = [tid for tid, t in zip(track_ids, resolved) if not t]

    return found, not_found


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

    playlist = sp.current_user_playlist_create(
        name,
        public=True,  # Must be public so users can access it
        description=description,
    )

    return playlist["id"]


def discard_playlist(playlist_id):
    """
    Remove a playlist from the system account.

    Unfollowing is Spotify's only delete: it orphans the playlist rather than
    erasing it. Never raises — callers use this while handling another error.

    Args:
        playlist_id: Spotify playlist ID
    """
    try:
        get_system_spotify().current_user_unfollow_playlist(playlist_id)
    except Exception as e:
        print(f"[SystemAccount] Could not discard playlist {playlist_id}: {e}")
