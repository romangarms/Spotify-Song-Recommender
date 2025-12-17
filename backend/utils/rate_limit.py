"""
Rate limiting utilities for playlist generation endpoints.

Uses in-memory storage for simplicity. For production with multiple
workers or distributed deployment, consider using Redis.
"""

import time
from functools import wraps
from flask import request, jsonify, current_app

# In-memory rate limit storage
# Format: {ip: [timestamp1, timestamp2, ...]}
rate_limit_store = {}


def check_rate_limit():
    """
    Check if the current IP has exceeded the rate limit.

    Returns:
        bool: True if rate limited, False otherwise
    """
    ip = request.remote_addr
    current_time = time.time()

    max_requests = current_app.config.get("RATE_LIMIT_MAX", 10)
    window = current_app.config.get("RATE_LIMIT_WINDOW", 3600)

    # Clean up old entries
    if ip in rate_limit_store:
        rate_limit_store[ip] = [
            t for t in rate_limit_store[ip]
            if current_time - t < window
        ]

    # Check limit
    if ip in rate_limit_store and len(rate_limit_store[ip]) >= max_requests:
        return True

    return False


def record_generation():
    """Record a playlist generation for rate limiting."""
    ip = request.remote_addr
    current_time = time.time()

    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    rate_limit_store[ip].append(current_time)


def rate_limit_required(f):
    """
    Decorator to apply rate limiting to a route.
    Returns 429 if rate limit exceeded.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if check_rate_limit():
            return jsonify({
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later."
            }), 429

        # Call the function
        result = f(*args, **kwargs)

        # Record the generation after successful call
        record_generation()

        return result

    return decorated_function
