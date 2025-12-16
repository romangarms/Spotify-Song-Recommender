"""
Profile API Blueprint

Handles user profile and playlist fetching endpoints.
"""

from flask import Blueprint, jsonify
from services.system_account import (
    parse_user_id_from_url,
    get_user_profile,
    get_user_public_playlists,
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
