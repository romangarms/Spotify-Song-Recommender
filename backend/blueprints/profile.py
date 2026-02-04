"""
Profile API Blueprint

Handles user profile and playlist fetching endpoints.
"""

from flask import Blueprint, jsonify, request
import spotipy
from services.system_account import (
    parse_user_id_from_url,
    get_user_profile,
    get_user_public_playlists,
    parse_playlist_id_from_url,
    get_system_spotify,
)

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile/<username>", methods=["GET"])
def get_profile(username):
    """
    Fetch a user's public profile by username or URL.

    Args:
        username: Spotify username, profile URL, or URI

    Returns:
        JSON: User profile with id, display_name, images, external_urls
    """
    # Parse user ID from various input formats
    user_id = parse_user_id_from_url(username)

    if not user_id:
        return jsonify({
            "error": "invalid_username",
            "message": "Invalid Spotify username or URL"
        }), 400

    try:
        profile = get_user_profile(user_id)
        return jsonify(profile)

    except ValueError as e:
        return jsonify({
            "error": "user_not_found",
            "message": str(e)
        }), 404

    except Exception as e:
        print(f"Error fetching profile: {e}")
        return jsonify({
            "error": "api_error",
            "message": "Failed to fetch profile from Spotify"
        }), 500


@profile_bp.route("/profile/<username>/playlists", methods=["GET"])
def get_playlists(username):
    """
    Fetch a user's public playlists.

    Args:
        username: Spotify username, profile URL, or URI

    Returns:
        JSON: Object with playlists array
    """
    # Parse user ID from various input formats
    user_id = parse_user_id_from_url(username)

    if not user_id:
        return jsonify({
            "error": "invalid_username",
            "message": "Invalid Spotify username or URL"
        }), 400

    try:
        playlists = get_user_public_playlists(user_id)
        # Sort alphabetically
        playlists.sort(key=lambda p: p["name"].lower())
        return jsonify({"playlists": playlists})

    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return jsonify({
            "error": "api_error",
            "message": "Failed to fetch playlists from Spotify"
        }), 500


@profile_bp.route("/playlist/owner", methods=["POST"])
def get_playlist_owner():
    """
    Extract owner username from a playlist URL.

    Request body:
        playlist_url: Spotify playlist URL or ID

    Returns:
        JSON: { username: str, display_name: str, playlist_name: str, playlist_id: str }
    """
    data = request.get_json()
    playlist_url = data.get("playlist_url", "").strip()

    if not playlist_url:
        return jsonify({
            "error": "missing_url",
            "message": "Playlist URL is required"
        }), 400

    try:
        # Extract playlist ID from URL
        playlist_id = parse_playlist_id_from_url(playlist_url)

        if not playlist_id:
            return jsonify({
                "error": "invalid_url",
                "message": "Invalid playlist URL. Please paste a valid Spotify playlist link."
            }), 400

        # Get playlist details via Spotify API
        sp = get_system_spotify()
        playlist = sp.playlist(playlist_id, fields="id,name,owner(id,display_name)")

        owner = playlist['owner']

        return jsonify({
            "username": owner['id'],
            "display_name": owner.get('display_name', owner['id']),
            "playlist_name": playlist['name'],
            "playlist_id": playlist['id']
        })

    except ValueError as e:
        return jsonify({
            "error": "invalid_url",
            "message": str(e)
        }), 400

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return jsonify({
                "error": "playlist_not_found",
                "message": "Playlist not found or is private"
            }), 404
        raise

    except Exception as e:
        print(f"Error getting playlist owner: {e}")
        return jsonify({
            "error": "api_error",
            "message": "Failed to get playlist information"
        }), 500


@profile_bp.route("/search/playlists", methods=["GET"])
def search_playlists():
    """
    Search for public playlists on Spotify.

    Query Parameters:
        q: Search query
        limit: Max results (default: 10, max: 20)

    Returns:
        JSON: { playlists: [...] }
    """
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({
            "error": "missing_query",
            "message": "Search query is required"
        }), 400

    if len(query) < 2:
        return jsonify({
            "error": "invalid_query",
            "message": "Query must be at least 2 characters"
        }), 400

    try:
        limit = min(int(request.args.get('limit', 10)), 20)
    except ValueError:
        limit = 10

    try:
        sp = get_system_spotify()
        results = sp.search(q=query, type='playlist', limit=limit)

        playlists = []
        for item in results['playlists']['items']:
            playlists.append({
                'id': item['id'],
                'name': item['name'],
                'owner': {
                    'id': item['owner']['id'],
                    'display_name': item['owner'].get('display_name', item['owner']['id'])
                },
                'image_url': item['images'][0]['url'] if item['images'] else None,
                'tracks_total': item['tracks']['total'],
                'url': item['external_urls']['spotify']
            })

        return jsonify({
            'playlists': playlists,
            'query': query,
            'count': len(playlists)
        })

    except Exception as e:
        print(f"Error searching playlists: {e}")
        return jsonify({
            "error": "search_error",
            "message": "Failed to search playlists"
        }), 500
