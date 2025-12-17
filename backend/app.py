"""
Spotify Song Recommender - Flask API Backend

This is the API backend for the React frontend. It provides JSON APIs
for profile fetching, playlist operations, and AI-powered playlist generation.

System Account Model:
- Users enter their Spotify profile URL (no OAuth login required)
- App fetches user's public playlists via system account
- Generated playlists are created on the system account
- Users receive a link to the generated playlist

Prerequisites:
    Install prereqs from requirements.txt

    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:5000/api/admin/callback'
    export LOGIC_API_TOKEN=logic_api_token_here
    export ADMIN_SECRET=your_secret_key_here
    export SPOTIFY_SYSTEM_REFRESH_TOKEN=xxx  # Set via admin setup

Run:
    python app.py
"""

import os
import sys
import pathlib

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_session import Session

from config import get_config

# Path to frontend build directory
FRONTEND_DIST = pathlib.Path(__file__).parent.parent / "frontend" / "dist"


def create_app(config_class=None):
    """
    Flask application factory.

    Args:
        config_class: Configuration class to use

    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]))
    Session(app)

    # Register blueprints
    from blueprints.profile import profile_bp
    from blueprints.generation import generation_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(generation_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"})

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "not_found",
            "message": "The requested resource was not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "internal_error",
            "message": "An internal server error occurred"
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        print(f"Unhandled error: {error}")
        return jsonify({
            "error": "internal_error",
            "message": str(error)
        }), 500

    # Serve React frontend static files (for non-API routes only)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # Don't serve frontend for API routes - let them 404 properly
        if path.startswith("api"):
            return jsonify({"error": "not_found", "message": "API endpoint not found"}), 404
        # If path exists as a file, serve it (JS, CSS, images, etc.)
        if path and (FRONTEND_DIST / path).exists():
            return send_from_directory(FRONTEND_DIST, path)
        # Otherwise serve index.html for client-side routing
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


def check_environment():
    """Check that required environment variables are set."""
    required_vars = [
        "SPOTIPY_CLIENT_ID",
        "SPOTIPY_CLIENT_SECRET",
        "SPOTIPY_REDIRECT_URI",
        "LOGIC_API_TOKEN",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Check for system refresh token (warn but don't exit)
    if not os.getenv("SPOTIFY_SYSTEM_REFRESH_TOKEN"):
        print("WARNING: SPOTIFY_SYSTEM_REFRESH_TOKEN not set.")
        print("Visit /api/admin/spotify-setup?key=YOUR_ADMIN_SECRET to configure.")


# Create the app instance
app = create_app()


if __name__ == "__main__":
    # Load .env from parent directory (project root)
    try:
        from dotenv import load_dotenv
        import pathlib
        env_path = pathlib.Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    check_environment()

    PORT = int(os.getenv("PORT", 5001))
    DEBUG = os.getenv("FLASK_ENV") != "production"

    if DEBUG:
        print(f"Running in development mode on http://127.0.0.1:{PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=True)
    else:
        from waitress import serve
        print(f"Running in production mode on http://0.0.0.0:{PORT}")
        serve(app, host="0.0.0.0", port=PORT)
