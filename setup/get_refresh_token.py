"""
One-time setup script: get a Spotify refresh token via OAuth.

Usage:
    export SPOTIFY_CLIENT_ID=your_id_here
    export SPOTIFY_CLIENT_SECRET=your_secret_here
    python setup/get_refresh_token.py

A browser window will open asking you to authorize the app.
After clicking Allow, your browser will try to load localhost (it will fail
to load — that's normal). Just paste the full URL from the address bar
back into this terminal.
"""

import os
import sys
import urllib.parse
import webbrowser
import spotipy.oauth2 as oauth2

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = " ".join([
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
])


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        missing = []
        if not client_id:
            missing.append("SPOTIFY_CLIENT_ID")
        if not client_secret:
            missing.append("SPOTIFY_CLIENT_SECRET")
        print("ERROR: Missing environment variables:", ", ".join(missing))
        print()
        print("Set them first:")
        print("  export SPOTIFY_CLIENT_ID=your_client_id_here")
        print("  export SPOTIFY_CLIENT_SECRET=your_client_secret_here")
        print()
        print("Get these from: https://developer.spotify.com/dashboard")
        print("  1. Create an app")
        print("  2. Add redirect URI: http://127.0.0.1:8888/callback")
        print("  3. Copy Client ID and Client Secret")
        sys.exit(1)

    auth_manager = oauth2.SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )

    auth_url = auth_manager.get_authorize_url()
    print("Opening Spotify authorization page in your browser...")
    print(f"If it doesn't open automatically, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    print("After clicking Allow, your browser will show an error page — that's normal.")
    print("Copy the full URL from your browser's address bar and paste it here.\n")
    callback_url = input("Paste the full redirect URL here: ").strip()

    if not callback_url:
        print("ERROR: No URL provided.")
        sys.exit(1)

    parsed = urllib.parse.urlparse(callback_url)
    params = urllib.parse.parse_qs(parsed.query)

    if "error" in params:
        print(f"ERROR: Spotify returned an error: {params['error'][0]}")
        sys.exit(1)

    if "code" not in params:
        print("ERROR: Could not find authorization code in URL.")
        print(f"  Got: {callback_url}")
        print("Make sure you copied the full URL from the address bar after clicking Allow.")
        sys.exit(1)

    auth_code = params["code"][0]

    try:
        token_info = auth_manager.exchange_code_for_token(auth_code)
    except Exception as exc:
        print(f"ERROR: Failed to exchange code for token: {exc}")
        sys.exit(1)

    refresh_token = token_info.get("refresh_token")
    if not refresh_token:
        print("ERROR: No refresh token in response. Unexpected Spotify error.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUCCESS! Your Spotify refresh token is:")
    print()
    print(f"  {refresh_token}")
    print()
    print("=" * 60)
    print()
    print("Add this to your Claude Desktop config (see README.md):")
    print('  "SPOTIFY_REFRESH_TOKEN": "' + refresh_token + '"')
    print()

    # Write a .env template for convenience
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.template")
    with open(env_path, "w") as f:
        f.write(f"SPOTIFY_CLIENT_ID={client_id}\n")
        f.write(f"SPOTIFY_CLIENT_SECRET={client_secret}\n")
        f.write(f"SPOTIFY_REFRESH_TOKEN={refresh_token}\n")
    print(f"Also saved to: {env_path}")


if __name__ == "__main__":
    main()
