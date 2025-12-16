"""
Configuration management for the Flask backend.
"""

import os


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.urandom(64)
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "./.flask_session/"
    TRAP_HTTP_EXCEPTIONS = True

    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]

    # Rate limiting
    RATE_LIMIT_MAX = 10  # Max generations per time window
    RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # In production, you'd want to set a fixed SECRET_KEY
    # SECRET_KEY = os.getenv("SECRET_KEY")


def get_config():
    """Get the appropriate configuration based on environment."""
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
