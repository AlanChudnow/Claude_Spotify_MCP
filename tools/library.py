"""
User library tools for SpotifyMCP.
"""

from spotify_client import get_client, with_retry


def spotify_get_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Get all tracks currently in a playlist, in order.

    Handles pagination automatically so playlists of any length are returned
    in full. Useful for inspecting what's already in a playlist before adding
    or reordering tracks.

    Parameters:
        playlist_id: Spotify playlist ID (from spotify_get_user_playlists).

    Returns:
        Ordered list of tracks with id, uri, name, artists, album, year,
        duration, spotify_url, and position (0-based index).

    Raises ValueError if the playlist is not found.
    """
    sp = get_client()
    tracks = []
    offset = 0
    limit = 100

    while True:
        def _fetch(off=offset):
            return sp.playlist_items(
                playlist_id,
                limit=limit,
                offset=off,
            )

        try:
            results = with_retry(_fetch)
        except Exception as exc:
            msg = str(exc).lower()
            if "not found" in msg or "404" in msg:
                raise ValueError(
                    f"Playlist not found: '{playlist_id}'. "
                    "Use spotify_get_user_playlists to find valid playlist IDs."
                ) from exc
            raise

        items = results.get("items", [])
        for i, item in enumerate(items):
            track = item.get("track") or item.get("item")
            if not track or not track.get("id"):
                continue
            artists = [a["name"] for a in track.get("artists", [])]
            album = track.get("album", {})
            release_date = album.get("release_date", "")
            year = release_date[:4] if release_date else ""
            duration_ms = track.get("duration_ms", 0)
            duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
            tracks.append({
                "position": offset + i,
                "id": track["id"],
                "uri": track["uri"],
                "name": track["name"],
                "artists": artists,
                "album": album.get("name", ""),
                "year": year,
                "duration": duration,
                "spotify_url": track.get("external_urls", {}).get("spotify", ""),
            })

        if not results.get("next"):
            break
        offset += limit

    return tracks
