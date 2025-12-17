"""
Logic API integration module.

This module contains functions to interact with the Logic API
for AI-powered playlist generation.
"""

import os
import requests
from .system_account import get_playlist_tracks
from .spotify import add_recommendations_to_playlist

# Logic API endpoints
LOGIC_PLAYLIST_FROM_TEXT_DOC = "https://api.logic.inc/2024-03-01/documents/generate-spotify-playlist-from-text"
LOGIC_PLAYLIST_FROM_PLAYLIST_DOC = "https://api.logic.inc/2024-03-01/documents/recommend-songs-from-playlist"


def generate_from_text(description, target_playlist_id):
    """
    Use the Logic API to generate a playlist from a text description.

    Args:
        description: Text description of the desired playlist
        target_playlist_id: Spotify playlist ID to populate

    Returns:
        dict: Result with keys: title, description, tracks, not_found

    Raises:
        ValueError: If description is empty
        Exception: If Logic API call fails
    """
    if not description:
        raise ValueError("Description is required")

    LOGIC_API_TOKEN = os.getenv("LOGIC_API_TOKEN")

    headers = {
        "Authorization": f"Bearer {LOGIC_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{LOGIC_PLAYLIST_FROM_TEXT_DOC}/executions",
        headers=headers,
        json={"description": description},
    )

    if response.status_code != 200:
        raise Exception(f"Logic API error: {response.text}")

    data = response.json()

    # Add tracks to playlist and return result
    result = add_recommendations_to_playlist(data, target_playlist_id)

    return result


def analyze_playlist(source_playlist_id, target_playlist_id):
    """
    Use the Logic API to analyze an existing playlist and generate recommendations.

    Args:
        source_playlist_id: Spotify playlist ID to analyze
        target_playlist_id: Spotify playlist ID to populate with recommendations

    Returns:
        dict: Result with keys: title, description, tracks, not_found

    Raises:
        ValueError: If source playlist cannot be accessed
        Exception: If Logic API call fails
    """
    # Fetch the source playlist tracks
    playlist = get_playlist_tracks(source_playlist_id)

    # Convert playlist to JSON format for Logic API
    tracks = playlist["tracks"]["items"]
    track_data = []

    for item in tracks:
        track = item.get("track")
        if not track:
            continue

        track_info = {
            "name": track["name"],
            "artist": track["artists"][0]["name"] if track["artists"] else "Unknown",
            "album": track["album"]["name"] if track.get("album") else "Unknown",
            "release_date": track["album"].get("release_date", "") if track.get("album") else "",
        }
        track_data.append(track_info)

    track_data_json = {"tracks": track_data}

    LOGIC_API_TOKEN = os.getenv("LOGIC_API_TOKEN")

    headers = {
        "Authorization": f"Bearer {LOGIC_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{LOGIC_PLAYLIST_FROM_PLAYLIST_DOC}/executions",
        headers=headers,
        json={"playlistJson": track_data_json},
    )

    if response.status_code != 200:
        raise Exception(f"Logic API error: {response.text}")

    data = response.json()

    # Add tracks to playlist and return result
    result = add_recommendations_to_playlist(data, target_playlist_id)

    return result
