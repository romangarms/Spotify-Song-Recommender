"""
Generation API Blueprint

Handles playlist generation endpoints.
"""

from flask import Blueprint, jsonify, request
from services.system_account import (
    parse_playlist_id_from_url,
    get_playlist_tracks,
    create_playlist_on_system_account,
)
from services.logic_api import analyze_playlist, generate_from_text
from utils.rate_limit import rate_limit_required

generation_bp = Blueprint("generation", __name__)


@generation_bp.route("/generate/test-rate-limit", methods=["POST"])
@rate_limit_required
def test_rate_limit():
    """
    Test endpoint to verify rate limiting without calling the Logic API.

    Returns:
        JSON: Mock playlist generation response
    """
    import time
    # Simulate a small delay like a real API call
    time.sleep(0.5)

    return jsonify({
        "playlist_id": "test_playlist_123",
        "playlist_url": "https://open.spotify.com/playlist/test_playlist_123",
        "title": "Test Rate Limit Playlist",
        "description": "This is a test response to verify rate limiting works correctly.",
        "tracks": [
            {
                "name": "Test Song 1",
                "artist": "Test Artist 1",
                "album": "Test Album",
                "spotify_url": "https://open.spotify.com/track/test1"
            },
            {
                "name": "Test Song 2",
                "artist": "Test Artist 2",
                "album": "Test Album",
                "spotify_url": "https://open.spotify.com/track/test2"
            }
        ],
        "not_found": []
    })


@generation_bp.route("/playlist/<playlist_id>/tracks", methods=["GET"])
def get_tracks(playlist_id):
    """
    Get tracks from a playlist.

    Args:
        playlist_id: Spotify playlist ID

    Returns:
        JSON: Object with name and tracks array
    """
    try:
        playlist = get_playlist_tracks(playlist_id)

        tracks = []
        for item in playlist["tracks"]["items"]:
            track = item.get("track")
            if not track:
                continue

            album = track.get("album", {})
            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track["artists"] else "Unknown",
                "album": album.get("name", "Unknown"),
                "image": album["images"][0]["url"] if album.get("images") else None,
            })

        return jsonify({
            "name": playlist.get("name"),
            "tracks": tracks
        })

    except ValueError as e:
        return jsonify({
            "error": "playlist_not_found",
            "message": str(e)
        }), 404

    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return jsonify({
            "error": "api_error",
            "message": "Failed to fetch playlist from Spotify"
        }), 500


@generation_bp.route("/playlist/validate", methods=["POST"])
def validate_playlist_url():
    """
    Validate a playlist URL and return playlist info.

    Request body:
        playlist_url: Spotify playlist URL or URI

    Returns:
        JSON: Object with playlist_id and playlist_name
    """
    data = request.get_json()
    playlist_url = data.get("playlist_url", "").strip()

    if not playlist_url:
        return jsonify({
            "error": "missing_url",
            "message": "Playlist URL is required"
        }), 400

    # Parse playlist ID
    playlist_id = parse_playlist_id_from_url(playlist_url)
    if not playlist_id:
        return jsonify({
            "error": "invalid_url",
            "message": "Invalid playlist URL. Please use a Spotify playlist link."
        }), 400

    try:
        playlist = get_playlist_tracks(playlist_id)
        return jsonify({
            "playlist_id": playlist_id,
            "playlist_name": playlist.get("name", "Unknown Playlist"),
            "tracks_total": playlist["tracks"]["total"],
            "images": playlist.get("images", [])
        })

    except ValueError as e:
        return jsonify({
            "error": "playlist_not_accessible",
            "message": str(e)
        }), 400

    except Exception as e:
        print(f"Error validating playlist: {e}")
        return jsonify({
            "error": "api_error",
            "message": "Couldn't access this playlist. Make sure it's public."
        }), 400


@generation_bp.route("/generate/from-playlist", methods=["POST"])
@rate_limit_required
def generate_from_playlist():
    """
    Generate a new playlist based on an existing playlist.

    Request body:
        playlist_id: Spotify playlist ID to analyze

    Returns:
        JSON: Generated playlist info with tracks
    """
    data = request.get_json()
    playlist_id = data.get("playlist_id")

    if not playlist_id:
        return jsonify({
            "error": "missing_playlist_id",
            "message": "playlist_id is required"
        }), 400

    try:
        # Create new playlist on system account
        new_playlist_id = create_playlist_on_system_account(
            "GEN: Work in Progress",
            "Being generated by the Logic API"
        )

        # Analyze source playlist and populate new playlist
        result = analyze_playlist(playlist_id, new_playlist_id)

        return jsonify({
            "playlist_id": new_playlist_id,
            "playlist_url": f"https://open.spotify.com/playlist/{new_playlist_id}",
            "title": result["title"],
            "description": result["description"],
            "tracks": result["tracks"],
            "not_found": result.get("not_found", [])
        })

    except ValueError as e:
        return jsonify({
            "error": "playlist_error",
            "message": str(e)
        }), 400

    except Exception as e:
        print(f"Error generating playlist: {e}")
        return jsonify({
            "error": "generation_error",
            "message": "Failed to generate playlist. Please try again."
        }), 500


@generation_bp.route("/generate/from-text", methods=["POST"])
@rate_limit_required
def generate_from_text_route():
    """
    Generate a new playlist based on a text description.

    Request body:
        description: Text description of desired playlist

    Returns:
        JSON: Generated playlist info with tracks
    """
    data = request.get_json()
    description = data.get("description", "").strip()

    if not description:
        return jsonify({
            "error": "missing_description",
            "message": "description is required"
        }), 400

    try:
        # Create new playlist on system account
        new_playlist_id = create_playlist_on_system_account(
            "GEN: Work in Progress",
            "Being generated by the Logic API"
        )

        # Generate playlist from text
        result = generate_from_text(description, new_playlist_id)

        return jsonify({
            "playlist_id": new_playlist_id,
            "playlist_url": f"https://open.spotify.com/playlist/{new_playlist_id}",
            "title": result["title"],
            "description": result["description"],
            "tracks": result["tracks"],
            "not_found": result.get("not_found", [])
        })

    except ValueError as e:
        return jsonify({
            "error": "generation_error",
            "message": str(e)
        }), 400

    except Exception as e:
        print(f"Error generating playlist from text: {e}")
        return jsonify({
            "error": "generation_error",
            "message": "Failed to generate playlist. Please try again."
        }), 500
