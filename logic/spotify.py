"""
This module contains functions to interact with the Spotify API.
It includes functions to add recommendations to a playlist,
get the current user's Spotify information, and fetch the selected playlist.
It also includes a function to get the user's liked songs
and simulate a playlist object for them.

The module uses the Spotipy library to interact with the Spotify API
"""

import time
import spotipy
from flask import session, redirect

# Spotify Constants:
RATE_LIMIT = 0.1  # seconds
# Spotify allows adding up to 100 tracks at once
SPOTIFY_ADD_LIMIT = 100
# Spotify allows fetching up to 50 saved tracks at once
SPOTIFY_SAVED_TRACKS_LIMIT = 50

# Settings
# How many liked songs to analyze?
LIKED_SONGS_ANALYZE_LIMIT = 200


def add_recommendations_to_playlist(response, playlist_id):
    """
    Given a list of LLM track recommendations, and a target Spotify `playlist_id`,
    this function searches for the recommended tracks on Spotify and adds them to the playlist.
    """

    recommendations = response["output"]["recommendations"]
    playlist_title = response["output"]["playlistTitle"]
    playlist_desc = response["output"]["playlistDesc"]
    sp = get_spotify()

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
                print(f"✅ Found: {name} by {artist}")
            else:
                not_found.append(f"{name} by {artist}")
                print(f"❌ Not found: {name} by {artist}")

        except Exception as e:
            not_found.append(f"{name} by {artist}")
            print(f"❌ Error searching {name} by {artist}: {e}")

        time.sleep(RATE_LIMIT)  # prevent rate-limiting

    if track_ids:
        try:
            # Spotify allows adding up to 100 tracks at once
            for i in range(0, len(track_ids), SPOTIFY_ADD_LIMIT):
                sp.playlist_add_items(playlist_id, track_ids[i : i + SPOTIFY_ADD_LIMIT])
            print(f"\n🎉 Added {len(track_ids)} track(s) to the playlist!")
        except Exception as e:
            print(f"🚨 Error adding tracks to playlist: {e}")

    if not_found:
        print("\n⚠️ The following tracks could not be found on Spotify:")
        for entry in not_found:
            print(f"  - {entry}")


def get_spotify():
    """Authenticate and return a Spotipy client instance."""

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist():
    """From a session variable, get the selected playlist from Spotify."""

    # Get the selected playlist ID from the session
    selected_playlist = session.get("selected_playlist")
    if not selected_playlist:
        return None

    sp = get_spotify()

    # Liked songs technically aren't a playlist, but we treat them as one
    # for the sake of this function
    if selected_playlist == "liked_songs":
        # Simulate a playlist object for Liked Songs
        liked_tracks = []

        offset = 0
        while True:
            results = sp.current_user_saved_tracks(
                limit=SPOTIFY_SAVED_TRACKS_LIMIT, offset=offset
            )
            items = results["items"]
            if not items:
                break
            liked_tracks.extend(items)
            offset += SPOTIFY_SAVED_TRACKS_LIMIT
            if len(liked_tracks) >= LIKED_SONGS_ANALYZE_LIMIT:
                break  # cap it if needed

        # Return a fake "playlist" object
        return {
            "name": "Liked Songs ❤️",
            "id": "liked_songs",
            "tracks": {"items": liked_tracks},
        }

    else:
        # Normal playlist
        return sp.playlist(selected_playlist)