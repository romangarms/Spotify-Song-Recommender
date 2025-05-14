import time
import spotipy
from flask import session, redirect

def add_recommendations_to_playlist(response, playlist_id):
    """
    Given a Spotipy client `sp`, a list of LLM track recommendations, and a target Spotify `playlist_id`,
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

        time.sleep(0.1)  # prevent rate-limiting

    if track_ids:
        try:
            # Spotify allows adding up to 100 tracks at once
            for i in range(0, len(track_ids), 100):
                sp.playlist_add_items(playlist_id, track_ids[i : i + 100])
            print(f"\n🎉 Added {len(track_ids)} track(s) to the playlist!")
        except Exception as e:
            print(f"🚨 Error adding tracks to playlist: {e}")

    if not_found:
        print("\n⚠️ The following tracks could not be found on Spotify:")
        for entry in not_found:
            print(f"  - {entry}")


def get_spotify():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist():
    # Get the selected playlist ID from the session
    selected_playlist = session.get("selected_playlist")
    if not selected_playlist:
        return None

    spotify = get_spotify()

    if selected_playlist == "liked_songs":
        # Simulate a playlist object for Liked Songs
        liked_tracks = []

        offset = 0
        while True:
            results = spotify.current_user_saved_tracks(limit=50, offset=offset)
            items = results["items"]
            if not items:
                break
            liked_tracks.extend(items)
            offset += 50
            if len(liked_tracks) >= 200:
                break  # cap it if needed

        # Return a fake "playlist" object
        return {
            "name": "Liked Songs ❤️",
            "id": "liked_songs",
            "tracks": {
                "items": liked_tracks
            }
        }

    else:
        # Normal playlist
        return spotify.playlist(selected_playlist)