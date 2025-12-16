"""
This module contains functions to interact with the Spotify API.
It includes functions to add recommendations to a playlist,
get the current user's Spotify information, and fetch the selected playlist.

The module uses the system account for all Spotify API calls.
Users don't authenticate directly - the system account is used to
fetch public data and create playlists.
"""

import time
from flask import session
from logic.system_account import get_system_spotify, get_playlist_tracks

# Spotify Constants:
RATE_LIMIT = 0.1  # seconds
# Spotify allows adding up to 100 tracks at once
SPOTIFY_ADD_LIMIT = 100


def add_recommendations_to_playlist(response, playlist_id):
    """
    Given a list of LLM track recommendations, and a target Spotify `playlist_id`,
    this function searches for the recommended tracks on Spotify and adds them to the playlist.

    Uses the system account to add tracks.
    """

    recommendations = response["output"]["recommendations"]
    playlist_title = response["output"]["playlistTitle"]
    playlist_desc = response["output"]["playlistDesc"]

    sp = get_system_spotify()

    sp.playlist_change_details(
        playlist_id, name=playlist_title, description=playlist_desc
    )

    track_ids = []
    not_found = []

    for rec in recommendations:
        name = rec.get("name")
        artist = rec.get("artist")
        query = f"track:{name} artist:{artist}"

        try:
            result = sp.search(q=query, type="track", limit=1)
            items = result["tracks"]["items"]
            if items:
                track_id = items[0]["id"]
                track_ids.append(track_id)
                print(f"Found: {name} by {artist}")
            else:
                not_found.append(f"{name} by {artist}")
                print(f"Not found: {name} by {artist}")

        except Exception as e:
            not_found.append(f"{name} by {artist}")
            print(f"Error searching {name} by {artist}: {e}")

        time.sleep(RATE_LIMIT)  # prevent rate-limiting

    if track_ids:
        try:
            # Spotify allows adding up to 100 tracks at once
            for i in range(0, len(track_ids), SPOTIFY_ADD_LIMIT):
                sp.playlist_add_items(playlist_id, track_ids[i : i + SPOTIFY_ADD_LIMIT])
            print(f"\nAdded {len(track_ids)} track(s) to the playlist!")
        except Exception as e:
            print(f"Error adding tracks to playlist: {e}")

    if not_found:
        print("\nThe following tracks could not be found on Spotify:")
        for entry in not_found:
            print(f"  - {entry}")


def get_playlist():
    """
    From a session variable, get the selected playlist from Spotify.

    Uses the system account to fetch public playlist data.
    """

    # Get the selected playlist ID from the session
    selected_playlist = session.get("selected_playlist")
    if not selected_playlist:
        return None

    try:
        # Fetch playlist using system account (works for any public playlist)
        playlist = get_playlist_tracks(selected_playlist)
        return playlist
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return None
