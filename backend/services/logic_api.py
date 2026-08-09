"""
Logic API integration module.

This module contains functions to interact with the Logic API
for AI-powered playlist generation.
"""

import os
import requests
from .spotify import add_recommendations_to_playlist

# Logic API endpoints
LOGIC_PLAYLIST_FROM_TEXT_DOC = "https://api.logic.inc/2024-03-01/documents/generate-spotify-playlist-from-text"
LOGIC_PLAYLIST_FROM_PLAYLIST_DOC = "https://api.logic.inc/2024-03-01/documents/recommend-songs-from-playlist"

LOGIC_TIMEOUT_SECONDS = 180
REQUIRED_OUTPUT_FIELDS = ("recommendations", "playlistTitle", "playlistDesc")


class LogicGenerationError(Exception):
    """The Logic document ran but declined to produce recommendations, e.g.
    because the seed songs are too obscure to ground suggestions in. The
    message is written for the user, not the operator."""


def extract_declined_reason(payload):
    """
    Pull the Logic document's own explanation out of an error payload.

    Args:
        payload: Parsed Logic API response

    Returns:
        str: Human-readable reason, or None if the payload has no explanation
    """
    error = payload.get("error")
    if not isinstance(error, dict):
        return None

    reasons = [str(e).strip() for e in error.get("errors") or [] if str(e).strip()]
    return " ".join(reasons) or None


def call_logic_document(document_url, payload):
    """
    Execute a Logic API document and return its validated output.

    Args:
        document_url: Base document URL
        payload: JSON body for the execution

    Returns:
        dict: The response JSON, guaranteed to carry a well-formed output

    Raises:
        Exception: If the call fails or the output is missing fields
    """
    response = requests.post(
        f"{document_url}/executions",
        headers={
            "Authorization": f"Bearer {os.getenv('LOGIC_API_TOKEN')}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=LOGIC_TIMEOUT_SECONDS,
    )

    try:
        data = response.json()
    except ValueError:
        raise Exception(
            f"Logic API returned non-JSON ({response.status_code}): "
            f"{response.text[:2000]}"
        )

    # A declined generation is the user's problem to fix, not a server fault,
    # so its reason is passed through rather than flattened into a 500.
    declined = extract_declined_reason(data)
    if declined:
        raise LogicGenerationError(declined)

    if response.status_code != 200:
        raise Exception(
            f"Logic API returned {response.status_code}: {response.text[:2000]}"
        )

    output = data.get("output")
    if not isinstance(output, dict):
        raise Exception(f"Logic API response has no output object: {str(data)[:2000]}")

    missing = [f for f in REQUIRED_OUTPUT_FIELDS if f not in output]
    if missing:
        raise Exception(
            f"Logic API output missing {', '.join(missing)}: {str(output)[:2000]}"
        )

    return data


def generate_from_text(description, target_playlist_id):
    """
    Use the Logic API to generate a playlist from a text description.

    Args:
        description: Text description of the desired playlist
        target_playlist_id: Spotify playlist ID to populate

    Returns:
        dict: Result with keys: title, description, tracks, not_found

    Raises:
        ValueError: If description is empty
        Exception: If Logic API call fails
    """
    if not description:
        raise ValueError("Description is required")

    data = call_logic_document(
        LOGIC_PLAYLIST_FROM_TEXT_DOC, {"description": description}
    )

    return add_recommendations_to_playlist(data, target_playlist_id)


def recommend_from_tracks(track_data, target_playlist_id):
    """
    Use the Logic API to generate recommendations from a list of seed tracks.

    Args:
        track_data: List of dicts with name, artist, album, release_date
        target_playlist_id: Spotify playlist ID to populate with recommendations

    Returns:
        dict: Result with keys: title, description, tracks, not_found

    Raises:
        ValueError: If no seed tracks were given
        Exception: If Logic API call fails
    """
    if not track_data:
        raise ValueError("At least one seed track is required")

    data = call_logic_document(
        LOGIC_PLAYLIST_FROM_PLAYLIST_DOC, {"playlistJson": {"tracks": track_data}}
    )

    return add_recommendations_to_playlist(data, target_playlist_id)


