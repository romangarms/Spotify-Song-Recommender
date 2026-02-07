"""
Rate limiting utilities for playlist generation endpoints.

Uses in-memory storage for simplicity. For production with multiple
workers or distributed deployment, consider using Redis.

Session-based tracking allows per-browser rate limiting without requiring login.
"""

import time
import uuid
from functools import wraps
from flask import request, jsonify, current_app, session

# In-memory rate limit storage
# Format: {session_id: [timestamp1, timestamp2, ...]}
rate_limit_store = {}


def get_session_id():
    """
    Get or create a session ID for anonymous users.

    Returns:
        str: Session ID for rate limiting
    """
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def check_rate_limit():
    """
    Check if the current session has exceeded the rate limit.

    Returns:
        tuple: (is_limited: bool, retry_after: int) where retry_after is seconds to wait
    """
    session_id = get_session_id()
    current_time = time.time()

    max_requests = current_app.config.get("RATE_LIMIT_MAX", 3)
    window = current_app.config.get("RATE_LIMIT_WINDOW", 60)

    # Clean up old entries
    if session_id in rate_limit_store:
        rate_limit_store[session_id] = [
            t for t in rate_limit_store[session_id]
            if current_time - t < window
        ]

    # Check limit
    if session_id in rate_limit_store and len(rate_limit_store[session_id]) >= max_requests:
        # Calculate time until oldest request expires
        oldest_request = min(rate_limit_store[session_id])
        retry_after = int(window - (current_time - oldest_request)) + 1
        return True, retry_after

    return False, 0


def record_generation():
    """Record a playlist generation for rate limiting."""
    session_id = get_session_id()
    current_time = time.time()

    if session_id not in rate_limit_store:
        rate_limit_store[session_id] = []

    rate_limit_store[session_id].append(current_time)


def rate_limit_required(f):
    """
    Decorator to apply rate limiting to a route.
    Returns 429 if rate limit exceeded.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_limited, retry_after = check_rate_limit()

        if is_limited:
            session_id = get_session_id()
            # Log rate limit violation (hash session_id for privacy)
            session_hash = hash(session_id) % 10000  # Simple hash for logging
            print(f"Rate limit violation - Session: {session_hash}, "
                  f"Endpoint: {request.endpoint}, "
                  f"Retry after: {retry_after}s")

            return jsonify({
                "error": "rate_limit_exceeded",
                "message": f"You've made too many requests. Please wait {retry_after} seconds before trying again.",
                "retry_after": retry_after
            }), 429

        # Call the function
        result = f(*args, **kwargs)

        # Record the generation after successful call
        record_generation()

        return result

    return decorated_function
