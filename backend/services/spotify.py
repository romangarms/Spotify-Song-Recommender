"""
Spotify API operations module.

This module contains functions to interact with the Spotify API
for searching tracks and adding them to playlists.

Uses the system account for all Spotify API calls.
"""

import time
from .system_account import get_system_spotify

# Spotify Constants
RATE_LIMIT = 0.1  # seconds between API calls
SPOTIFY_ADD_LIMIT = 100  # Spotify allows adding up to 100 tracks at once


def search_and_get_tracks(recommendations):
    """
    Search for tracks on Spotify and return their details.

    Args:
        recommendations: List of dicts with 'name' and 'artist' keys

    Returns:
        tuple: (found_tracks, not_found)
            - found_tracks: List of track dicts with id, name, artist, album, image
            - not_found: List of strings describing tracks not found
    """
    sp = get_system_spotify()
    found_tracks = []
    not_found = []

    for rec in recommendations:
        name = rec.get("name")
        artist = rec.get("artist")
        query = f"track:{name} artist:{artist}"

        try:
            result = sp.search(q=query, type="track", limit=1)
            items = result["tracks"]["items"]

            if items:
                track = items[0]
                album = track["album"]
                found_tracks.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": album["name"],
                    "image": album["images"][0]["url"] if album["images"] else None,
                })
                print(f"Found: {name} by {artist}")
            else:
                not_found.append(f"{name} by {artist}")
                print(f"Not found: {name} by {artist}")

        except Exception as e:
            not_found.append(f"{name} by {artist}")
            print(f"Error searching {name} by {artist}: {e}")

        time.sleep(RATE_LIMIT)  # prevent rate-limiting

    return found_tracks, not_found


def add_recommendations_to_playlist(response, playlist_id):
    """
    Given a Logic API response with recommendations, search for the tracks
    on Spotify and add them to the specified playlist.

    Args:
        response: Logic API response dict with output.recommendations
        playlist_id: Target Spotify playlist ID

    Returns:
        dict: Result with keys: title, description, tracks, not_found
    """
    recommendations = response["output"]["recommendations"]
    playlist_title = response["output"]["playlistTitle"]
    playlist_desc = response["output"]["playlistDesc"]

    sp = get_system_spotify()

    # Update playlist name and description
    sp.playlist_change_details(
        playlist_id, name=playlist_title, description=playlist_desc
    )

    # Search for tracks
    found_tracks, not_found = search_and_get_tracks(recommendations)

    # Add tracks to playlist
    if found_tracks:
        track_ids = [t["id"] for t in found_tracks]
        try:
            # Spotify allows adding up to 100 tracks at once
            for i in range(0, len(track_ids), SPOTIFY_ADD_LIMIT):
                sp.playlist_add_items(playlist_id, track_ids[i:i + SPOTIFY_ADD_LIMIT])
            print(f"\nAdded {len(track_ids)} track(s) to the playlist!")
        except Exception as e:
            print(f"Error adding tracks to playlist: {e}")

    if not_found:
        print("\nThe following tracks could not be found on Spotify:")
        for entry in not_found:
            print(f"  - {entry}")

    return {
        "title": playlist_title,
        "description": playlist_desc,
        "tracks": found_tracks,
        "not_found": not_found,
    }
