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

import os
from flask import Flask, session, request, redirect, render_template, jsonify
from flask_session import Session
import spotipy
import sys

from logic.spotify import get_spotify, get_playlist
from logic.logic_api import analyze_playlist_with_logic, make_playlist_from_text_with_logic

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
app.config['TRAP_HTTP_EXCEPTIONS']=True
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

@app.errorhandler(Exception)
def http_error_handler(error):
    return render_template("error.html", error=error), 500


@app.route("/")
def index():
    #print(os.getenv("SPOTIPY_CLIENT_ID"))
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope="playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-read",
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

    # ✅ Add Liked Songs as a special "playlist"
    playlists.insert(0, {"name": "Liked Songs ❤️", "id": "liked_songs"})

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
