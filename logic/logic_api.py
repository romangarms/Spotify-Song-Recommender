"""
This module contains functions to interact with the Logic API.
It includes functions to create a playlist from a text description
or from an existing playlist.
"""

from flask import session, redirect
import requests
import os
from logic.spotify import get_playlist, add_recommendations_to_playlist

# Set these to the Logic API endpoints for your specific documents. You can find the document templates in the /logic_documents folder.
LOGIC_PLAYLIST_FROM_TEXT_DOC = "https://api.logic.inc/2024-03-01/documents/generate-spotify-playlist-from-text"
LOGIC_PLAYLIST_FROM_PLAYLIST_DOC = "https://api.logic.inc/2024-03-01/documents/recommend-songs-from-playlist"

def make_playlist_from_text_with_logic():
    """
    Use the Logic API to create a playlist from a text description
    """

    new_playlist = session.get("new_playlist")
    text_description = session.get("playlist_description")

    if not new_playlist and not text_description:
        return None

    print("text retrieved")

    LOGIC_API_TOKEN = os.getenv("LOGIC_API_TOKEN")

    headers = {
        "Authorization": f"Bearer {LOGIC_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{LOGIC_PLAYLIST_FROM_TEXT_DOC}/executions",
        headers=headers,
        json={"description": text_description},
    )

    session["newPlaylistTitle"] = response.json()["output"]["playlistTitle"]
    add_recommendations_to_playlist(response.json(), new_playlist)
    return redirect("/playlist_from_text")


def analyze_playlist_with_logic():
    """
    Use the Logic API to analyze the selected playlist and generate a new playlist
    """

    template_playlist = session.get("selected_playlist")
    new_playlist = session.get("new_playlist")
    t_playlist = None

    if new_playlist and template_playlist:
        # Fetch the playlist details using Spotipy
        t_playlist = get_playlist()
    else:
        return None

    print("playlists retrieved")

    # convert playlist to json of track names, artists names, album names, and release date
    tracks = t_playlist["tracks"]["items"]
    track_data = []
    for track in tracks:
        track_info = {
            "name": track["track"]["name"],
            # only read the first artist
            "artist": track["track"]["artists"][0]["name"],
            "album": track["track"]["album"]["name"],
            "release_date": track["track"]["album"]["release_date"],
        }
        track_data.append(track_info)
    # convert to json
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

    session["newPlaylistTitle"] = response.json()["output"]["playlistTitle"]
    session["newPlaylistDescription"] = response.json()["output"]["playlistDesc"]
    add_recommendations_to_playlist(response.json(), new_playlist)
    return redirect("playlist_from_playlist")