"""
Validation script: checks that SpotifyMCP is correctly configured and can
connect to Spotify before you add it to Claude Desktop.

Usage:
    python setup/check_setup.py
"""

import os
import sys

# Allow running from the repo root or the setup/ subdirectory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def check():
    print("Checking SpotifyMCP setup...\n")

    # 1. Load credentials (file takes priority over env vars)
    from spotify_client import load_credentials, KEYS_FILE
    creds = load_credentials()
    client_id = creds["SPOTIFY_CLIENT_ID"]
    client_secret = creds["SPOTIFY_CLIENT_SECRET"]
    refresh_token = creds["SPOTIFY_REFRESH_TOKEN"]

    if os.path.exists(KEYS_FILE):
        print(f"  [OK] Credentials file found: {KEYS_FILE}")
    else:
        print(f"  [WARN] No credentials file at {KEYS_FILE} — falling back to env vars")

    all_ok = True
    for name, val in [
        ("SPOTIFY_CLIENT_ID", client_id),
        ("SPOTIFY_CLIENT_SECRET", client_secret),
        ("SPOTIFY_REFRESH_TOKEN", refresh_token),
    ]:
        if val:
            print(f"  [OK] {name} is set")
        else:
            print(f"  [ERROR] {name} is NOT set")
            all_ok = False

    if not all_ok:
        print()
        print("Fix missing credentials, then run this script again.")
        print("Call the spotify_setup tool in Claude Desktop, or see README.md.")
        sys.exit(1)

    print()

    # 2. Try to authenticate and fetch user profile
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        from spotipy.cache_handler import MemoryCacheHandler
    except ImportError:
        print("[ERROR] spotipy is not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    SCOPES = " ".join([
        "playlist-read-private",
        "playlist-modify-public",
        "playlist-modify-private",
    ])

    token_info = {
        "access_token": "",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": SCOPES,
        "expires_at": 0,
    }
    cache_handler = MemoryCacheHandler(token_info=token_info)
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=SCOPES,
        cache_handler=cache_handler,
        open_browser=False,
    )

    try:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user = sp.current_user()
        display_name = user.get("display_name") or user.get("id", "unknown")
        print(f"[OK] Connected as: {display_name}")
        print()
        print("All tests passed — restart Claude Desktop to apply changes")
        print()
        print("Run 'python server.py --test' for a full end-to-end playlist test.")
    except spotipy.SpotifyException as exc:
        if exc.http_status in (401, 403):
            print("[ERROR] Authentication failed.")
            print("   Your refresh token may be expired or invalid.")
            print("   Call the spotify_setup tool in Claude Desktop to re-authenticate.")
        else:
            print(f"[ERROR] Spotify API error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    check()
