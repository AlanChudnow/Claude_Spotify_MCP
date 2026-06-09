"""
Playlist creation and management tools for SpotifyMCP.
"""

from spotify_client import get_client, with_retry



def spotify_create_playlist(
    name: str,
    description: str = "",
    public: bool = False,
) -> dict:
    """
    Create a new empty playlist in the user's Spotify account.

    Parameters:
        name: Playlist name.
        description: Optional description shown in Spotify.
        public: Whether the playlist is public (default False = private).

    Returns:
        Dict with playlist_id, name, spotify_url.
    """
    sp = get_client()

    def _create():
        return sp._post(
            "me/playlists",
            payload={"name": name, "public": public, "description": description},
        )

    playlist = with_retry(_create)
    return {
        "playlist_id": playlist["id"],
        "name": playlist["name"],
        "spotify_url": playlist.get("external_urls", {}).get("spotify", ""),
    }


def spotify_add_tracks(playlist_id: str, track_uris: list[str]) -> dict:
    """
    Add tracks to an existing playlist, handling Spotify's 100-track batch limit.

    Parameters:
        playlist_id: Spotify playlist ID (from spotify_get_user_playlists or
                     spotify_create_playlist).
        track_uris: List of Spotify track URIs (e.g. 'spotify:track:xxxx').

    Returns:
        Dict with playlist_id and tracks_added count.

    Raises ValueError if the playlist is not found.
    """
    if not track_uris:
        return {"playlist_id": playlist_id, "tracks_added": 0}

    sp = get_client()
    added = 0
    batch_size = 100

    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i : i + batch_size]

        def _add(b=batch):
            sp.playlist_add_items(playlist_id, b)

        try:
            with_retry(_add)
        except Exception as exc:
            msg = str(exc).lower()
            if "not found" in msg or "404" in msg:
                raise ValueError(
                    f"Playlist not found: '{playlist_id}'. "
                    "Use spotify_get_user_playlists to find valid playlist IDs."
                ) from exc
            raise
        added += len(batch)

    return {"playlist_id": playlist_id, "tracks_added": added}


def spotify_create_playlist_with_tracks(
    name: str,
    description: str = "",
    track_uris: list[str] | None = None,
    public: bool = False,
) -> dict:
    """
    Create a playlist AND add tracks in a single call.

    This is the primary tool to use when the user says 'put this in Spotify'
    or 'create this playlist'. Combines spotify_create_playlist and
    spotify_add_tracks for convenience.

    Parameters:
        name: Playlist name.
        description: Optional description.
        track_uris: List of Spotify track URIs to add immediately.
        public: Whether the playlist is public (default False).

    Returns:
        Dict with playlist_id, name, track_count, spotify_url.
    """
    track_uris = track_uris or []
    playlist = spotify_create_playlist(name=name, description=description, public=public)
    playlist_id = playlist["playlist_id"]

    if track_uris:
        spotify_add_tracks(playlist_id=playlist_id, track_uris=track_uris)

    return {
        "playlist_id": playlist_id,
        "name": playlist["name"],
        "track_count": len(track_uris),
        "spotify_url": playlist["spotify_url"],
    }


def spotify_get_user_playlists(limit: int = 20) -> list[dict]:
    """
    List the current user's Spotify playlists.

    Parameters:
        limit: How many playlists to return (1–50, default 20).

    Returns:
        List of playlists with id, name, track_count, description, spotify_url.
    """
    limit = max(1, min(50, limit))
    sp = get_client()

    def _list():
        return sp.current_user_playlists(limit=limit)

    results = with_retry(_list)
    playlists = []
    for p in results.get("items", []):
        playlists.append({
            "id": p["id"],
            "name": p["name"],
            "track_count": p.get("tracks", {}).get("total", 0),
            "description": p.get("description", ""),
            "spotify_url": p.get("external_urls", {}).get("spotify", ""),
        })
    return playlists


def spotify_reorder_tracks(
    playlist_id: str,
    range_start: int,
    insert_before: int,
) -> dict:
    """
    Move a track (or block of tracks) to a different position in a playlist.

    Useful for arranging historical/chronological playlists after creation.
    Positions are 0-indexed.

    Parameters:
        playlist_id: Spotify playlist ID.
        range_start: Current 0-based index of the track to move.
        insert_before: Target 0-based index (the track will be placed before this position).

    Returns:
        Dict with playlist_id and confirmation message.
    """
    sp = get_client()

    def _reorder():
        sp.playlist_reorder_items(
            playlist_id=playlist_id,
            range_start=range_start,
            insert_before=insert_before,
        )

    try:
        with_retry(_reorder)
    except Exception as exc:
        msg = str(exc).lower()
        if "not found" in msg or "404" in msg:
            raise ValueError(
                f"Playlist not found: '{playlist_id}'. "
                "Use spotify_get_user_playlists to find valid playlist IDs."
            ) from exc
        raise

    return {
        "playlist_id": playlist_id,
        "message": f"Moved track at position {range_start} to before position {insert_before}.",
    }
