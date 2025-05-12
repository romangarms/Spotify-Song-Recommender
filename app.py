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
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy
import sys

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
    return redirect("/main")


@app.route("/sign_out")
def sign_out():
    session.pop("token_info", None)
    return redirect("/")


@app.route("/main")
def currently_playing():
    spotify = get_spotify()
    return render_template("main.html")
    

@app.errorhandler(HTTPException)
def handle_exception(e):
    # Handle HTTP exceptions
    return render_template("error.html", error=e), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    # Handle other exceptions
    return render_template("error.html", error=e), e.code


def get_spotify():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/")
    return spotipy.Spotify(auth_manager=auth_manager)


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
