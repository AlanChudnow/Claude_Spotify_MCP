"""
Spotify API wrapper — handles authentication and all API calls.
Uses Spotipy with Authorization Code Flow + refresh token.
Token refresh is automatic and silent via Spotipy's CacheHandler.
"""

import json
import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler


SCOPES = " ".join([
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
])

KEYS_FILE = r"C:\Users\Daddy\.key\Spotify.json"

_client: spotipy.Spotify | None = None


def load_credentials() -> dict:
    """
    Load Spotify credentials with file taking priority over env vars.
    Supports both flat format and nested SpotifyKeys.SpotifyMCP format.
    Returns a dict with SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN.
    """
    # Start with env vars as base
    creds = {
        "SPOTIFY_CLIENT_ID": os.environ.get("SPOTIFY_CLIENT_ID", ""),
        "SPOTIFY_CLIENT_SECRET": os.environ.get("SPOTIFY_CLIENT_SECRET", ""),
        "SPOTIFY_REFRESH_TOKEN": os.environ.get("SPOTIFY_REFRESH_TOKEN", ""),
    }

    # Override with file values (file takes priority)
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r") as f:
                data = json.load(f)
            # Support nested format: {"SpotifyKeys": {"SpotifyMCP": {...}}}
            if "SpotifyKeys" in data and "SpotifyMCP" in data["SpotifyKeys"]:
                file_creds = data["SpotifyKeys"]["SpotifyMCP"]
            else:
                file_creds = data
            for key in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"):
                if file_creds.get(key):
                    creds[key] = file_creds[key]
        except Exception:
            pass

    return creds


def save_credentials(client_id: str, client_secret: str, refresh_token: str) -> None:
    """Save credentials to the keys file, preserving nested structure."""
    data = {}
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if "SpotifyKeys" not in data:
        data["SpotifyKeys"] = {}
    data["SpotifyKeys"]["SpotifyMCP"] = {
        "SPOTIFY_CLIENT_ID": client_id,
        "SPOTIFY_CLIENT_SECRET": client_secret,
        "SPOTIFY_REFRESH_TOKEN": refresh_token,
    }

    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _make_token_info(refresh_token: str) -> dict:
    """Build a minimal token_info dict that Spotipy accepts."""
    return {
        "access_token": "",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": SCOPES,
        "expires_at": 0,  # already expired → Spotipy will refresh immediately
    }


def get_client() -> spotipy.Spotify:
    """Return a cached, authenticated Spotipy client, refreshing as needed."""
    global _client
    if _client is not None:
        return _client

    creds = load_credentials()
    client_id = creds["SPOTIFY_CLIENT_ID"]
    client_secret = creds["SPOTIFY_CLIENT_SECRET"]
    refresh_token = creds["SPOTIFY_REFRESH_TOKEN"]

    missing = [
        name for name, val in [
            ("SPOTIFY_CLIENT_ID", client_id),
            ("SPOTIFY_CLIENT_SECRET", client_secret),
            ("SPOTIFY_REFRESH_TOKEN", refresh_token),
        ] if not val
    ]
    if missing:
        raise RuntimeError(
            f"Missing Spotify credentials: {', '.join(missing)}. "
            "Call the spotify_setup tool to fix this — no terminal required."
        )

    cache_handler = MemoryCacheHandler(token_info=_make_token_info(refresh_token))
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=SCOPES,
        cache_handler=cache_handler,
        open_browser=False,
    )

    _client = spotipy.Spotify(auth_manager=auth_manager)
    return _client


def reset_client() -> None:
    """Force a new client on the next call (used after auth errors)."""
    global _client
    _client = None


def with_retry(fn, *args, max_retries: int = 3, **kwargs):
    """
    Call fn(*args, **kwargs) with exponential backoff on rate-limit (429) errors.
    Re-raises on other errors after one retry for transient network issues.
    """
    delay = 1.0
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except spotipy.SpotifyException as exc:
            last_exc = exc
            if exc.http_status == 429:
                retry_after = int(exc.headers.get("Retry-After", delay)) if exc.headers else delay
                time.sleep(retry_after)
                delay *= 2
            elif exc.http_status in (401, 403):
                reset_client()
                raise RuntimeError(
                    "Spotify authentication failed. Call the spotify_setup tool to fix this — "
                    "no terminal required."
                ) from exc
            else:
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise
        except Exception as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(1)
                continue
            raise RuntimeError(f"Network error: {exc}") from exc
    raise RuntimeError(f"Spotify request failed after {max_retries} retries: {last_exc}")
