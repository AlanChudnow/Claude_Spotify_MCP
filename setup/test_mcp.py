"""
End-to-end test for SpotifyMCP — validates auth and full playlist workflow.

Usage:
    python setup/test_mcp.py
    python server.py --test
"""

import io
import os
import sys
from datetime import datetime

# Ensure emoji characters print correctly on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Allow running from the repo root or the setup/ subdirectory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_tests():
    step = 0
    playlist_id = None

    try:
        # ── Step 1: Credential loading ────────────────────────────────────────
        step = 1
        from spotify_client import load_credentials, KEYS_FILE

        if not os.path.exists(KEYS_FILE):
            raise RuntimeError(f"{KEYS_FILE} not found")

        creds = load_credentials()
        missing = [
            k for k in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN")
            if not creds.get(k)
        ]
        if missing:
            raise RuntimeError(f"Missing keys in credentials file: {', '.join(missing)}")

        print("✅ Credentials loaded from spotify.json")

        # ── Step 2: Spotify authentication ───────────────────────────────────
        step = 2
        from spotify_client import get_client, with_retry

        sp = get_client()
        try:
            user = with_retry(sp.current_user)
        except Exception as exc:
            print(f"❌ Authentication error: {exc}")
            sys.exit(1)

        display_name = user.get("display_name") or user.get("id", "unknown")
        email = user.get("email", "no email")
        print(f"✅ Authenticated as: {display_name} ({email})")

        # Verify the token has playlist-modify scope before attempting write ops
        token_info = sp.auth_manager.get_cached_token()
        token_scope = token_info.get("scope", "") if token_info else ""
        required_write_scopes = ["playlist-modify-public", "playlist-modify-private"]
        missing_scopes = [s for s in required_write_scopes if s not in token_scope]
        if missing_scopes:
            raise RuntimeError(
                f"Token is missing required scopes: {', '.join(missing_scopes)}. "
                "Re-run setup/get_refresh_token.py to obtain a token with full playlist access."
            )

        # ── Step 3: Track search ──────────────────────────────────────────────
        step = 3
        from tools.search import spotify_search_tracks

        results = spotify_search_tracks("artist:Aerosmith Train Kept a Rollin", limit=5)
        if not results:
            raise RuntimeError("Search returned no results")

        first = results[0]
        uri = first.get("uri", "")
        if not uri.startswith("spotify:track:"):
            raise RuntimeError(f"Invalid URI in search result: {uri!r}")

        print(f"✅ Search works — found: {first['name']}")

        # ── Step 4: Playlist creation ─────────────────────────────────────────
        step = 4
        from tools.playlists import spotify_create_playlist

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        playlist_name = f"SpotifyMCP Test — {timestamp}"
        playlist = spotify_create_playlist(
            name=playlist_name,
            description="Automated test playlist — safe to delete",
        )

        playlist_id = playlist.get("playlist_id")
        if not playlist_id:
            raise RuntimeError("Playlist creation returned no playlist_id")

        print(f"✅ Playlist created: {playlist['name']} (id: {playlist_id})")

        # ── Step 5: Adding tracks ─────────────────────────────────────────────
        step = 5
        from tools.playlists import spotify_add_tracks

        TEST_URI = "spotify:track:6zb4VGZE20uKHc0mydFgR5"
        add_result = spotify_add_tracks(
            playlist_id=playlist_id,
            track_uris=[TEST_URI],
        )

        if add_result.get("tracks_added") != 1:
            raise RuntimeError(
                f"Expected tracks_added == 1, got {add_result.get('tracks_added')}"
            )

        print("✅ Track added successfully")

        # ── Step 6: Playlist readback ─────────────────────────────────────────
        step = 6
        from tools.library import spotify_get_playlist_tracks

        tracks = spotify_get_playlist_tracks(playlist_id)
        if len(tracks) != 1:
            raise RuntimeError(f"Expected 1 track in playlist, got {len(tracks)}")

        track_name = tracks[0].get("name", "")
        if "Train" not in track_name:
            raise RuntimeError(
                f"Expected track name to contain 'Train', got {track_name!r}"
            )

        print(f"✅ Playlist readback confirmed: {track_name}")

        # ── Step 7: Cleanup ───────────────────────────────────────────────────
        step = 7
        with_retry(sp.current_user_unfollow_playlist, playlist_id)
        playlist_id = None
        print("✅ Test playlist deleted")

    except Exception as exc:
        # Best-effort cleanup if we created a playlist but haven't deleted it
        if playlist_id:
            try:
                from spotify_client import get_client, with_retry
                sp = get_client()
                with_retry(sp.current_user_unfollow_playlist, playlist_id)
                print("✅ Test playlist deleted (cleanup after failure)")
            except Exception:
                pass
        print(f"\n❌ TESTS FAILED at step {step}: {exc}\n")
        sys.exit(1)

    print("\n🎉 ALL TESTS PASSED — SpotifyMCP is fully operational\n")
    sys.exit(0)


if __name__ == "__main__":
    run_tests()
