"""
CS50 Final Project: Spotify Status - Roman Garms

Prerequisites

    Install prereqs from requirements.txt

    // from your [app settings](https://developer.spotify.com/dashboard/applications)

    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:5000' // must contain a port

    // set the redirect url to 'http://127.0.0.1:5000' for testing on your local machine. When hosting, you will need to change that to the address of the device you are hosting on.
    // SPOTIPY_REDIRECT_URI must be added to your [app settings](https://developer.spotify.com/dashboard/applications)
    // on Windows, use `SET` instead of `export`

Run app.py
    python3 app.py OR python3 -m flask run
    Alternatively, run using the launch.json under .vscode/ with the VSCode debugger
"""

from http.client import HTTPException
import os
from flask import Flask, session, request, redirect, render_template, jsonify
from flask_session import Session
import spotipy
import sys
import requests
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)
debug = True

if debug:
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()  # take environment variables from .env.


@app.route("/debug")
def debug():
    spotify = get_spotify()
    playlists = spotify.current_user_playlists()
    # Debugging route to check session data
    return playlists


@app.route("/")
def index():
    #print(os.getenv("SPOTIPY_CLIENT_ID"))
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public",
        cache_handler=cache_handler,
        show_dialog=False,
    )

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template("login.html", auth_url=auth_url)

    # Step 3. Signed in, main page
    return redirect("playlist_from_playlist")


@app.route("/sign_out")
def sign_out():
    session.clear()
    session.pop("token_info", None)
    return redirect("/")


@app.route("/playlist_from_playlist")
def playlist_analyzer():

    spotify = get_spotify()
    # get user playlists
    results = spotify.current_user_playlists()

    username = spotify.me()["display_name"]

    pfp = spotify.me()["images"][0]["url"] if spotify.me()["images"] else None

    # trim down the results to only the name and id of the playlist
    playlists = [{"name": item["name"], "id": item["id"]} for item in results["items"]]

    playlist = get_playlist()
    new_playlist = session.get("new_playlist")

    playlist_name = None
    if playlist:
        # fetch playlist's name
        playlist_name = playlist["name"]

    if new_playlist:
        # fetch playlist's name
        new_playlist_name = session.get("newPlaylistTitle")
        new_playlist_url = f"https://open.spotify.com/playlist/{new_playlist}"
        new_playlist_description = session.get("newPlaylistDescription")
    else:
        new_playlist_name = "No new playlist created, generate one?"
        new_playlist_url = None
        new_playlist_description = "No playlist description available"

    return render_template(
        "playlist_from_playlist.html",
        playlists=playlists,
        playlist_name=playlist_name,
        new_playlist_name=new_playlist_name,
        new_playlist_url=new_playlist_url,
        new_playlist_description=new_playlist_description,
        username=username,
        pfp=pfp,
    )


@app.route("/playlist_from_text")
def playlist_maker():

    spotify = get_spotify()
    username = spotify.me()["display_name"]

    new_playlist = session.get("new_playlist")

    pfp = spotify.me()["images"][0]["url"] if spotify.me()["images"] else None

    if new_playlist:
        # fetch playlist's name
        new_playlist_name = session.get("newPlaylistTitle")
        new_playlist_url = f"https://open.spotify.com/playlist/{new_playlist}"
        new_playlist_description = session.get("newPlaylistDescription")

    else:
        new_playlist_name = "No new playlist created, generate one?"
        new_playlist_url = None
        new_playlist_description = "No playlist description available"


    return render_template(
        "playlist_from_text.html",
        new_playlist_name=new_playlist_name,
        new_playlist_url=new_playlist_url,
        new_playlist_description=new_playlist_description,
        username=username,
        pfp=pfp,
    )


@app.route("/describe_playlist", methods=["POST"])
def describe_playlist():
    data = request.get_json()
    description = data.get("description")

    session["playlist_description"] = description

    if description:
        session["playlist_description"] = description  # Save it per user
        return jsonify({"status": "ok", "saved": description})
    return jsonify({"status": "error", "message": "No description provided"}), 400


@app.route("/select_playlist", methods=["POST"])
def select_playlist():
    data = request.get_json()
    playlist_id = data["playlist_id"]

    print(f"Selected playlist ID: {playlist_id}")

    # Store in the session (per-user, per-browser)
    session["selected_playlist"] = playlist_id

    # You could now analyze this playlist or save it to session, etc.
    print(f"User selected playlist ID: {playlist_id}")

    return jsonify({"status": "ok", "selected": playlist_id})


@app.route("/generate-from-text", methods=["POST"])
def generate_from_text():
    """
    Generate a playlist from a text description
    """
    create_playlist("text")
    return redirect("/playlist_from_text")


@app.route("/generate-from-playlist", methods=["POST"])
def generate_from_playlist():
    """
    Generate a playlist from a selected playlist
    """
    create_playlist("playlist")
    return redirect("/playlist_from_playlist")


@app.route("/create_playlist", methods=["POST"])
def create_playlist(mode="playlist"):
    # data = request.get_json()
    playlist_name = "GEN: Work in Progress"
    playlist_description = "Being generated by the Logic API"

    # Create a new playlist
    spotify = get_spotify()
    user_id = spotify.me()["id"]
    new_playlist = spotify.user_playlist_create(
        user_id, playlist_name, public=False, description=playlist_description
    )

    session["new_playlist"] = new_playlist["id"]

    if mode == "playlist":
        # go hit the logic API and generate the playlist
        analyze_playlist_with_logic()
    elif mode == "text":
        # go hit the logic API and generate the playlist
        make_playlist_from_text_with_logic()

    return redirect("/playlist_from_playlist")


def make_playlist_from_text_with_logic():
    """
    Use the Logic API to create a playlist from a text description
    """

    new_playlist = session.get("new_playlist")
    text_description = session.get("playlist_description")

    if new_playlist and text_description:
        # Fetch the playlist details using Spotipy
        spotify = get_spotify()
    else:
        return None

    print("text retrieved")

    LOGIC_API_TOKEN = os.getenv("LOGIC_API_TOKEN")

    headers = {
        "Authorization": f"Bearer {LOGIC_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.logic.inc/2024-03-01/documents/recommend-songs-from-playlist/executions",
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
        spotify = get_spotify()
        t_playlist = spotify.playlist(template_playlist)
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
        "https://api.logic.inc/2024-03-01/documents/recommend-songs-from-playlist/executions",
        headers=headers,
        json={"playlistJson": track_data_json},
    )

    session["newPlaylistTitle"] = response.json()["output"]["playlistTitle"]
    session["newPlaylistDescription"] = response.json()["output"]["playlistDesc"]
    add_recommendations_to_playlist(response.json(), new_playlist)
    return redirect("playlist_from_playlist")


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

    if selected_playlist:
        # Fetch the playlist details using Spotipy
        spotify = get_spotify()
        playlist = spotify.playlist(selected_playlist)
        return playlist
    else:
        return None


"""
Following lines allow application to be run more conveniently with
`python3 app.py` (Make sure you're using python3)
"""
if __name__ == "__main__":
    if os.getenv("SPOTIPY_CLIENT_ID") == None:
        sys.exit("Missing Environment Variable: SPOTIPY_CLIENT_ID")
    if os.getenv("SPOTIPY_CLIENT_SECRET") == None:
        sys.exit("Missing Environment Variable: SPOTIPY_CLIENT_SECRET")
    if os.getenv("SPOTIPY_REDIRECT_URI") == None:
        sys.exit("Missing Environment Variable: SPOTIPY_REDIRECT_URI")
    print(os.getenv("SPOTIPY_REDIRECT_URI"))
    from waitress import serve

    serve(app, host="0.0.0.0", port=8100)
