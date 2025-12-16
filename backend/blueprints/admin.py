"""
Admin API Blueprint

Handles admin routes for system account OAuth setup.
"""

import os
from flask import Blueprint, request, redirect, jsonify
import spotipy

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/spotify-setup", methods=["GET"])
def admin_spotify_setup():
    """
    Admin route to initiate OAuth flow for system account.
    Requires admin secret key in query params.

    Query params:
        key: Admin secret key (must match ADMIN_SECRET env var)

    Returns:
        Redirect to Spotify OAuth URL
    """
    admin_secret = os.getenv("ADMIN_SECRET")
    provided_key = request.args.get("key")

    # Debug logging
    print(f"[Admin] ADMIN_SECRET set: {bool(admin_secret)}")
    if admin_secret:
        print(f"[Admin] ADMIN_SECRET length: {len(admin_secret)}, starts with: {admin_secret[:4]}...")
    print(f"[Admin] Provided key: {bool(provided_key)}")
    if provided_key:
        print(f"[Admin] Provided key length: {len(provided_key)}, starts with: {provided_key[:4]}...")
    if admin_secret and provided_key:
        print(f"[Admin] Keys match: {admin_secret == provided_key}")

    if not admin_secret:
        return jsonify({
            "error": "config_error",
            "message": "ADMIN_SECRET environment variable not set"
        }), 500

    if not provided_key or provided_key != admin_secret:
        return jsonify({
            "error": "unauthorized",
            "message": "Invalid or missing admin key"
        }), 401

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


@admin_bp.route("/callback", methods=["GET"])
def admin_callback():
    """
    OAuth callback for system account setup.
    Returns the refresh token for the admin to copy.

    Query params:
        code: OAuth authorization code

    Returns:
        JSON: Object with refresh_token
    """
    code = request.args.get("code")
    if not code:
        return jsonify({
            "error": "missing_code",
            "message": "No authorization code received"
        }), 400

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

        # Return the refresh token as JSON
        return jsonify({
            "success": True,
            "refresh_token": refresh_token,
            "message": "Copy this refresh token and set it as SPOTIFY_SYSTEM_REFRESH_TOKEN environment variable"
        })

    except Exception as e:
        return jsonify({
            "error": "token_error",
            "message": f"Error getting token: {str(e)}"
        }), 500
