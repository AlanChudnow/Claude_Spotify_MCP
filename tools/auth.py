"""
spotify_setup — self-healing OAuth tool.
Handles the full Spotify auth flow from inside the Claude chat window.
"""

import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler

import spotify_client


SCOPES = spotify_client.SCOPES
REDIRECT_URI = "http://127.0.0.1:8888/callback"
_callback_code: str | None = None
_callback_error: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _callback_code, _callback_error
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _callback_code = params["code"][0]
            body = b"<h2>Spotify connected! You can close this tab and return to Claude.</h2>"
        else:
            _callback_error = params.get("error", ["unknown"])[0]
            body = b"<h2>Authorization failed. Return to Claude for details.</h2>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress server logs


def spotify_setup(client_id: str = "", client_secret: str = "") -> str:
    """
    Set up or repair Spotify authentication without leaving the chat window.

    Call this tool if you see any Spotify authentication errors, or on first
    use to connect to Spotify. It will open the browser for a one-time login,
    then save credentials so you never need to do this again.

    Parameters:
        client_id: Spotify app Client ID (only needed on first setup).
                   Get this from developer.spotify.com/dashboard
        client_secret: Spotify app Client Secret (only needed on first setup).
    """
    global _callback_code, _callback_error

    # Load whatever we already have on disk/env
    creds = spotify_client.load_credentials()

    # Fill in any values passed by the user
    if client_id:
        creds["SPOTIFY_CLIENT_ID"] = client_id
    if client_secret:
        creds["SPOTIFY_CLIENT_SECRET"] = client_secret

    # Prompt for missing app credentials
    if not creds["SPOTIFY_CLIENT_ID"]:
        return (
            "SpotifyMCP needs your Spotify app credentials to get started.\n\n"
            "1. Go to https://developer.spotify.com/dashboard\n"
            "2. Open your app (or create one)\n"
            "3. Copy the Client ID and call this tool again:\n\n"
            "   spotify_setup(client_id=\"YOUR_CLIENT_ID\", client_secret=\"YOUR_CLIENT_SECRET\")"
        )
    if not creds["SPOTIFY_CLIENT_SECRET"]:
        return (
            "I have your Client ID but still need the Client Secret.\n\n"
            "Find it in your Spotify app dashboard and call:\n\n"
            f"   spotify_setup(client_id=\"{creds['SPOTIFY_CLIENT_ID']}\", "
            "client_secret=\"YOUR_CLIENT_SECRET\")"
        )

    # Reset callback state
    _callback_code = None
    _callback_error = None

    # Build auth manager (open_browser=False — we open it manually)
    auth_manager = SpotifyOAuth(
        client_id=creds["SPOTIFY_CLIENT_ID"],
        client_secret=creds["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_handler=MemoryCacheHandler(),
        open_browser=False,
    )

    auth_url = auth_manager.get_authorize_url()

    # Start local callback server
    server = HTTPServer(("127.0.0.1", 8888), _CallbackHandler)
    server.timeout = 120  # 2-minute window for the user to log in

    webbrowser.open(auth_url)

    # Wait for the callback (blocking, up to timeout)
    server.handle_request()
    server.server_close()

    if _callback_error:
        return f"Authorization was denied or failed: {_callback_error}. Please try again."

    if not _callback_code:
        return (
            "No callback received within 2 minutes. "
            "Please call spotify_setup again and complete the browser login promptly."
        )

    # Exchange code for tokens
    try:
        token_info = auth_manager.exchange_code_for_token(_callback_code)
    except Exception as exc:
        return f"Failed to exchange authorization code for tokens: {exc}"

    refresh_token = token_info.get("refresh_token", "")
    if not refresh_token:
        return "Spotify returned tokens but no refresh token. Please try again."

    # Persist to .key file
    spotify_client.save_credentials(
        creds["SPOTIFY_CLIENT_ID"],
        creds["SPOTIFY_CLIENT_SECRET"],
        refresh_token,
    )

    # Reload the live client
    spotify_client.reset_client()

    # Verify connection and get username
    try:
        sp = spotify_client.get_client()
        user = sp.current_user()
        display_name = user.get("display_name") or user.get("id", "unknown")
    except Exception as exc:
        return (
            f"Credentials saved, but test connection failed: {exc}\n"
            "Restart Claude Desktop and try again."
        )

    return (
        f"Spotify connected successfully as {display_name}. "
        "You're ready to create playlists."
    )
