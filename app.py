"""
Spotify Song Recommender - Roman Garms

System Account Model:
- Users enter their Spotify profile URL (no OAuth login required)
- App fetches user's public playlists via system account
- Generated playlists are created on the system account
- Users receive a link to the generated playlist

Prerequisites:

    Install prereqs from requirements.txt

    // from your [app settings](https://developer.spotify.com/dashboard/applications)

    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:5000/admin/callback'
    export LOGIC_API_TOKEN=logic_api_token_here
    export ADMIN_SECRET=your_secret_key_here
    export SPOTIFY_SYSTEM_REFRESH_TOKEN=xxx  # Set via admin setup

Run app.py
    python3 app.py OR python3 -m flask run
"""

import os
import time
from functools import wraps
from flask import Flask, session, request, redirect, render_template, jsonify
from flask_session import Session
import spotipy

from logic.system_account import (
    parse_user_id_from_url,
    parse_playlist_id_from_url,
    get_user_profile,
    get_user_public_playlists,
    get_playlist_tracks,
    create_playlist_on_system_account,
)
from logic.logic_api import (
    analyze_playlist_with_logic,
    make_playlist_from_text_with_logic,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
app.config["TRAP_HTTP_EXCEPTIONS"] = True
Session(app)

# Settings
PORT = 5000
DEBUG = True

# Rate limiting: track playlist generations per IP
# Format: {ip: [(timestamp1), (timestamp2), ...]}
rate_limit_store = {}
RATE_LIMIT_MAX = 10  # Max generations per time window
RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)

if DEBUG:
    from dotenv import load_dotenv
    load_dotenv()


def require_profile(f):
    """Decorator to require user profile in session before accessing route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_profile"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def check_rate_limit():
    """
    Check if the current IP has exceeded the rate limit.
    Returns True if rate limited, False otherwise.
    """
    ip = request.remote_addr
    current_time = time.time()

    # Clean up old entries
    if ip in rate_limit_store:
        rate_limit_store[ip] = [
            t for t in rate_limit_store[ip]
            if current_time - t < RATE_LIMIT_WINDOW
        ]

    # Check limit
    if ip in rate_limit_store and len(rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return True

    return False


def record_generation():
    """Record a playlist generation for rate limiting."""
    ip = request.remote_addr
    current_time = time.time()

    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    rate_limit_store[ip].append(current_time)


@app.errorhandler(Exception)
def http_error_handler(error):
    """Handle HTTP errors and display a custom error page."""
    print(f"Error: {error}")
    return render_template("error.html", error=error), 500


# =============================================================================
# Landing Page & Profile Setup
# =============================================================================

@app.route("/")
def index():
    """
    Landing page: Users enter their Spotify profile URL to begin.
    If already have a profile in session, redirect to main page.
    """
    # If user already has a profile, go to main page
    if session.get("user_profile"):
        return redirect("/playlist_from_playlist")

    error = request.args.get("error")
    return render_template("landing.html", error=error)


@app.route("/set_profile", methods=["POST"])
def set_profile():
    """
    Process the profile URL submitted on the landing page.
    Fetches user's public profile and playlists.
    """
    profile_url = request.form.get("profile_url", "").strip()

    # Parse user ID from URL
    user_id = parse_user_id_from_url(profile_url)
    if not user_id:
        return redirect("/?error=invalid_url")

    try:
        # Fetch user profile using system account
        profile = get_user_profile(user_id)

        # Store in session
        session["user_profile"] = profile
        session["user_id"] = user_id

        return redirect("/playlist_from_playlist")

    except ValueError as e:
        return redirect(f"/?error=user_not_found")
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return redirect(f"/?error=api_error")


@app.route("/sign_out")
def sign_out():
    """Clear session and return to landing page."""
    session.clear()
    return redirect("/")


# =============================================================================
# Playlist from Playlist
# =============================================================================

@app.route("/playlist_from_playlist")
@require_profile
def playlist_analyzer():
    """Generate a playlist from analyzing a selected playlist."""
    profile = session.get("user_profile")
    user_id = session.get("user_id")

    # Get profile picture
    pfp = profile["images"][0]["url"] if profile.get("images") else None
    username = profile.get("display_name", user_id)

    # Fetch user's public playlists
    try:
        playlists = get_user_public_playlists(user_id)
        playlists.sort(key=lambda p: p["name"].lower())
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        playlists = []

    # Get selected playlist name
    selected_playlist = session.get("selected_playlist")
    playlist_name = None
    if selected_playlist:
        # Find the name from our playlists list
        for p in playlists:
            if p["id"] == selected_playlist:
                playlist_name = p["name"]
                break

    # Check for external playlist URL selection
    if session.get("external_playlist_name"):
        playlist_name = session.get("external_playlist_name")

    # Get generated playlist info
    new_playlist = session.get("new_playlist")
    if new_playlist:
        new_playlist_name = session.get("newPlaylistTitle", "Generated Playlist")
        new_playlist_url = f"https://open.spotify.com/playlist/{new_playlist}"
        new_playlist_description = session.get("newPlaylistDescription", "")
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


@app.route("/select_playlist", methods=["POST"])
@require_profile
def select_playlist():
    """Save the selected playlist ID in the session."""
    data = request.get_json()
    playlist_id = data.get("playlist_id")

    if not playlist_id:
        return jsonify({"status": "error", "message": "No playlist ID provided"}), 400

    # Clear any external playlist URL selection
    session.pop("external_playlist_url", None)
    session.pop("external_playlist_name", None)

    session["selected_playlist"] = playlist_id
    print(f"User selected playlist ID: {playlist_id}")

    return jsonify({"status": "ok", "selected": playlist_id})


@app.route("/set_playlist_url", methods=["POST"])
@require_profile
def set_playlist_url():
    """Set a playlist URL as the source playlist."""
    data = request.get_json()
    playlist_url = data.get("playlist_url", "").strip()

    if not playlist_url:
        # Clear the external playlist selection
        session.pop("external_playlist_url", None)
        session.pop("external_playlist_name", None)
        session.pop("selected_playlist", None)
        return jsonify({"status": "ok", "cleared": True})

    # Parse playlist ID from URL
    playlist_id = parse_playlist_id_from_url(playlist_url)
    if not playlist_id:
        return jsonify({
            "status": "error",
            "message": "Invalid playlist URL. Please use a Spotify playlist link."
        }), 400

    # Verify playlist is accessible
    try:
        playlist = get_playlist_tracks(playlist_id)
        playlist_name = playlist.get("name", "External Playlist")

        # Store both the URL and the parsed ID
        session["external_playlist_url"] = playlist_url
        session["external_playlist_name"] = playlist_name
        session["selected_playlist"] = playlist_id

        return jsonify({
            "status": "ok",
            "playlist_id": playlist_id,
            "playlist_name": playlist_name
        })

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return jsonify({
            "status": "error",
            "message": "Couldn't access this playlist. Make sure it's public."
        }), 400


@app.route("/generate-from-playlist", methods=["POST"])
@require_profile
def generate_from_playlist():
    """Generate a playlist from a selected playlist."""
    # Check rate limit
    if check_rate_limit():
        return render_template(
            "error.html",
            error="Rate limit exceeded. Please try again later."
        ), 429

    selected_playlist = session.get("selected_playlist")
    if not selected_playlist:
        return redirect("/playlist_from_playlist")

    # Create playlist and generate
    create_playlist("playlist")
    record_generation()

    return redirect("/playlist_from_playlist")


# =============================================================================
# Playlist from Text
# =============================================================================

@app.route("/playlist_from_text")
@require_profile
def playlist_maker():
    """Generate a playlist from a text description."""
    profile = session.get("user_profile")
    user_id = session.get("user_id")

    pfp = profile["images"][0]["url"] if profile.get("images") else None
    username = profile.get("display_name", user_id)

    new_playlist = session.get("new_playlist")
    if new_playlist:
        new_playlist_name = session.get("newPlaylistTitle", "Generated Playlist")
        new_playlist_url = f"https://open.spotify.com/playlist/{new_playlist}"
        new_playlist_description = session.get("newPlaylistDescription", "")
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
@require_profile
def describe_playlist():
    """Save the playlist description from text input."""
    data = request.get_json()
    description = data.get("description")

    if description:
        session["playlist_description"] = description
        return jsonify({"status": "ok", "saved": description})

    return jsonify({"status": "error", "message": "No description provided"}), 400


@app.route("/generate-from-text", methods=["POST"])
@require_profile
def generate_from_text():
    """Generate a playlist from a text description."""
    # Check rate limit
    if check_rate_limit():
        return render_template(
            "error.html",
            error="Rate limit exceeded. Please try again later."
        ), 429

    description = session.get("playlist_description")
    if not description:
        return redirect("/playlist_from_text")

    create_playlist("text")
    record_generation()

    return redirect("/playlist_from_text")


# =============================================================================
# Playlist Creation
# =============================================================================

def create_playlist(mode="playlist"):
    """
    Create a new playlist on the system account and populate it.

    Args:
        mode: "playlist" to analyze existing playlist, "text" for text-based generation
    """
    playlist_name = "GEN: Work in Progress"
    playlist_description = "Being generated by the Logic API"

    # Create playlist on system account
    new_playlist_id = create_playlist_on_system_account(
        playlist_name,
        playlist_description
    )

    session["new_playlist"] = new_playlist_id

    if mode == "playlist":
        analyze_playlist_with_logic()
    elif mode == "text":
        make_playlist_from_text_with_logic()

    return new_playlist_id


# =============================================================================
# Admin Routes for System Account Setup
# =============================================================================

@app.route("/admin/spotify-setup")
def admin_spotify_setup():
    """
    Admin route to initiate OAuth flow for system account.
    Requires admin secret key in query params.
    """
    admin_secret = os.getenv("ADMIN_SECRET")
    provided_key = request.args.get("key")

    if not admin_secret:
        return "ADMIN_SECRET environment variable not set", 500

    if not provided_key or provided_key != admin_secret:
        return "Unauthorized", 401

    # Create OAuth manager for system account setup
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private user-read-private",
        show_dialog=True,
    )

    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)


@app.route("/admin/callback")
def admin_callback():
    """
    OAuth callback for system account setup.
    Displays the refresh token for the admin to copy.
    """
    code = request.args.get("code")
    if not code:
        return "No authorization code received", 400

    # Exchange code for tokens
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private user-read-private",
    )

    try:
        token_info = auth_manager.get_access_token(code)
        refresh_token = token_info.get("refresh_token")

        # Display the refresh token
        return render_template("admin_token.html", refresh_token=refresh_token)

    except Exception as e:
        return f"Error getting token: {e}", 500


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    required_vars = [
        "SPOTIPY_CLIENT_ID",
        "SPOTIPY_CLIENT_SECRET",
        "SPOTIPY_REDIRECT_URI",
        "LOGIC_API_TOKEN",
    ]

    for var in required_vars:
        if not os.getenv(var):
            import sys
            sys.exit(f"Missing Environment Variable: {var}")

    # Check for system refresh token (warn but don't exit)
    if not os.getenv("SPOTIFY_SYSTEM_REFRESH_TOKEN"):
        print("WARNING: SPOTIFY_SYSTEM_REFRESH_TOKEN not set.")
        print("Visit /admin/spotify-setup?key=YOUR_ADMIN_SECRET to configure.")

    from waitress import serve
    print(f"Running on http://127.0.0.1:{PORT}")
    serve(app, host="0.0.0.0", port=PORT)
