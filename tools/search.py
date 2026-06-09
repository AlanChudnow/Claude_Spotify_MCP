"""
Search tools for SpotifyMCP.

Key note on alternate titles: many tracks appear on Spotify under different names
than they're commonly known. For example, the Yardbirds' version of "Train Kept A-Rollin'"
appears as "Stroll On" in the film Blow Up. Always search by both the original title
AND any known alternate titles before concluding a track isn't on Spotify.
"""

from typing import Any
from spotify_client import get_client, with_retry


def _format_track(track: dict) -> dict:
    """Normalize a Spotipy track object to our standard shape."""
    artists = [a["name"] for a in track.get("artists", [])]
    album = track.get("album", {})
    release_date = album.get("release_date", "")
    year = release_date[:4] if release_date else ""
    duration_ms = track.get("duration_ms", 0)
    duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
    return {
        "id": track["id"],
        "uri": track["uri"],
        "name": track["name"],
        "artists": artists,
        "album": album.get("name", ""),
        "year": year,
        "duration": duration,
        "spotify_url": track.get("external_urls", {}).get("spotify", ""),
    }


def spotify_search_tracks(query: str, limit: int = 10) -> list[dict]:
    """
    Search Spotify for tracks by title, artist, album, year, or genre.

    Supports Spotify's advanced search operators, e.g.:
      - 'artist:Yardbirds year:1965-1966'
      - 'Stroll On artist:Yardbirds'
      - 'Train Kept A-Rollin year:1951-1960'

    Use this to explore multiple candidates before picking the best match.
    When a track might have alternate titles (e.g. "Stroll On" = "Train Kept A-Rollin'"),
    search both titles.

    Parameters:
        query: Search string. Can be a plain title/artist or use Spotify field filters.
        limit: Number of results to return (1–50, default 10).

    Returns:
        List of tracks with id, uri, name, artists, album, year, duration, spotify_url.
    """
    limit = max(1, min(50, limit))
    sp = get_client()

    def _search():
        return sp.search(q=query, type="track", limit=limit)

    try:
        results = with_retry(_search)
    except RuntimeError:
        raise

    items = results.get("tracks", {}).get("items", [])
    if not items:
        return []
    return [_format_track(t) for t in items]


def spotify_search_album(artist: str, album_name: str) -> dict:
    """
    Find a specific album and return its full track listing with URIs.

    Especially useful for classical music where you need a particular
    recording, conductor, or ensemble. Returns the best-matching album
    plus all its tracks in order.

    Parameters:
        artist: Artist, composer, or ensemble name.
        album_name: Album title (partial matches are fine).

    Returns:
        Dict with album details (name, artists, year, spotify_url, total_tracks)
        and a 'tracks' list with full details for each track.
    """
    sp = get_client()
    query = f"artist:{artist} album:{album_name}"

    def _search():
        return sp.search(q=query, type="album", limit=5)

    try:
        results = with_retry(_search)
    except RuntimeError:
        raise

    albums = results.get("albums", {}).get("items", [])
    if not albums:
        raise ValueError(
            f"No album found for artist '{artist}', album '{album_name}'. "
            "Try broader search terms or check the artist name spelling."
        )

    album = albums[0]
    album_id = album["id"]

    def _get_tracks():
        return sp.album_tracks(album_id, limit=50)

    tracks_result = with_retry(_get_tracks)
    track_items = tracks_result.get("items", [])

    # album_tracks returns simplified track objects — enrich with full details
    track_ids = [t["id"] for t in track_items if t.get("id")]

    def _get_full():
        return sp.tracks(track_ids)

    full_tracks = with_retry(_get_full).get("tracks", []) if track_ids else []
    id_to_full = {t["id"]: t for t in full_tracks if t}

    formatted_tracks = []
    for t in track_items:
        full = id_to_full.get(t.get("id"))
        if full:
            formatted_tracks.append(_format_track(full))
        else:
            artists = [a["name"] for a in t.get("artists", [])]
            duration_ms = t.get("duration_ms", 0)
            duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
            formatted_tracks.append({
                "id": t.get("id", ""),
                "uri": t.get("uri", ""),
                "name": t.get("name", ""),
                "artists": artists,
                "album": album.get("name", ""),
                "year": album.get("release_date", "")[:4],
                "duration": duration,
                "spotify_url": t.get("external_urls", {}).get("spotify", ""),
            })

    release_date = album.get("release_date", "")
    return {
        "name": album["name"],
        "artists": [a["name"] for a in album.get("artists", [])],
        "year": release_date[:4] if release_date else "",
        "total_tracks": album.get("total_tracks", len(formatted_tracks)),
        "spotify_url": album.get("external_urls", {}).get("spotify", ""),
        "tracks": formatted_tracks,
    }


def spotify_find_track(
    artist: str,
    title: str,
    prefer_original: bool = True,
) -> dict:
    """
    Smart single-track lookup: find the best Spotify match for a known song.

    Handles common problems:
    - Slight title differences ("Stroll On" vs "Train Kept A-Rollin'")
    - Remastered/live/compilation variants (prefer_original=True picks earliest release)
    - Multiple artists with the same song name

    Always try both the primary title AND any known alternate titles before
    concluding a track isn't available.

    Parameters:
        artist: Artist name (required).
        title: Song title. Use the most well-known version of the title.
        prefer_original: If True, prefer the earliest release date over remasters
                         or greatest-hits compilations (default True).

    Returns:
        Dict with:
          - 'best_match': the single best track found (full details)
          - 'alternates': list of other candidates found (up to 9)
        Raises ValueError if no match is found at all.
    """
    sp = get_client()

    queries = [
        f"artist:{artist} track:{title}",
        f"{title} {artist}",
        f"artist:{artist} {title}",
    ]

    candidates: list[dict] = []
    seen_ids: set[str] = set()

    for q in queries:
        def _search(query=q):
            return sp.search(q=query, type="track", limit=10)

        try:
            results = with_retry(_search)
        except RuntimeError:
            raise

        for t in results.get("tracks", {}).get("items", []):
            if t["id"] not in seen_ids:
                seen_ids.add(t["id"])
                candidates.append(t)

    if not candidates:
        raise ValueError(
            f"No results found for '{title}' by '{artist}'. "
            "Try searching with just the artist name, or check for alternate titles."
        )

    def sort_key(t: dict):
        release_date = t.get("album", {}).get("release_date", "9999")
        year = int(release_date[:4]) if release_date[:4].isdigit() else 9999
        # Penalize remasters/live/greatest hits in album name
        album_name = t.get("album", {}).get("name", "").lower()
        is_remaster = any(w in album_name for w in ["remaster", "remastered", "greatest", "best of", "collection", "live"])
        return (is_remaster, year if prefer_original else -year)

    candidates.sort(key=sort_key)
    best = _format_track(candidates[0])
    alternates = [_format_track(t) for t in candidates[1:10]]

    return {
        "best_match": best,
        "alternates": alternates,
    }
