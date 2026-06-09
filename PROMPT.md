# SpotifyMCP — Build Instructions

## Project Overview

Build a Python MCP (Model Context Protocol) server called **SpotifyMCP** that connects
Claude Desktop to Spotify. The goal is to allow Claude to intelligently research, curate,
and create playlists directly in the user's Spotify account.

---

## The User Experience

The user will have conversations with Claude like:

> "Create a playlist that tells the history of 'Train Kept A-Rollin' — start with Tiny
> Bradshaw's 1951 original, through Johnny Burnette's rockabilly version, the Yardbirds
> with Jeff Beck, the rare Beck + Page version called 'Stroll On' from the film Blow Up,
> then Aerosmith, then Motörhead."

Claude will:
1. Research and identify the specific tracks and any alternate titles (e.g. "Stroll On"
   is "Train Kept A-Rollin'" with different lyrics — the user would never find it
   by searching the original title)
2. Search Spotify for each track, handling title variations and alternate names
3. Present the proposed playlist with track details for user approval
4. When the user says "put this in Spotify" — create the playlist and add the tracks

---

## Technical Requirements

### Language & Frameworks
- **Python 3.10+**
- **FastMCP** for the MCP server framework (`pip install fastmcp`)
- **Spotipy** for Spotify API access (`pip install spotipy`)
- No TypeScript, no Node.js, no build step required

### Authentication
- Spotify OAuth 2.0 using the **Authorization Code Flow** with refresh token
- Credentials stored in environment variables (never hardcoded):
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REFRESH_TOKEN`
- Token refresh must be handled automatically and silently — the user should never
  need to re-authenticate after initial setup
- Required Spotify scopes:
  - `playlist-read-private`
  - `playlist-modify-public`
  - `playlist-modify-private`

### Project Structure

```
SpotifyMCP/
├── PROMPT.md                  # This file
├── README.md                  # Setup and usage instructions
├── requirements.txt           # Python dependencies
├── server.py                  # Main MCP server entry point
├── spotify_client.py          # Spotify API wrapper (auth + all API calls)
├── tools/
│   ├── __init__.py
│   ├── search.py              # Search-related tools
│   ├── playlists.py           # Playlist creation and management tools
│   └── library.py             # User library tools
└── setup/
    ├── get_refresh_token.py   # One-time OAuth setup script
    └── check_setup.py         # Validates all env vars and connectivity
```

---

## MCP Tools to Implement

### Search Tools (`tools/search.py`)

**`spotify_search_tracks`**
- Search Spotify for tracks by any combination of: song title, artist name, album,
  year range, genre
- Parameters: `query` (string), `limit` (int, default 10, max 50)
- Returns: list of tracks with `id`, `name`, `artists`, `album`, `year`, `uri`,
  `duration`, `spotify_url`
- Important: search should support Spotify's advanced operators when useful
  (e.g. `artist:Yardbirds year:1965-1966`)

**`spotify_search_album`**
- Search for a specific album to find its tracks
- Parameters: `artist` (string), `album_name` (string)
- Returns: album details and full track listing with URIs
- Useful for classical music where you want a specific recording/conductor

**`spotify_find_track`**
- Smarter single-track lookup: given an artist and song title, find the best
  matching track on Spotify
- Should handle common issues: slight title differences, remastered versions,
  compilation appearances
- Parameters: `artist` (string), `title` (string), `prefer_original` (bool,
  default True — prefer earliest release over remasters)
- Returns: single best match with full details, plus list of alternates found

### Playlist Tools (`tools/playlists.py`)

**`spotify_create_playlist`**
- Create a new empty playlist in the user's account
- Parameters: `name` (string), `description` (string, optional),
  `public` (bool, default False)
- Returns: `playlist_id`, `name`, `spotify_url`

**`spotify_add_tracks`**
- Add tracks to an existing playlist
- Parameters: `playlist_id` (string), `track_uris` (list of strings)
- Handles Spotify's 100-track-per-request limit automatically by batching
- Returns: confirmation with count of tracks added

**`spotify_create_playlist_with_tracks`**
- Convenience tool: create a playlist AND add tracks in one call
- Parameters: `name` (string), `description` (string), `track_uris` (list),
  `public` (bool, default False)
- This is the tool Claude should use when the user says "put this in Spotify"
- Returns: `playlist_id`, `name`, `track_count`, `spotify_url`

**`spotify_get_user_playlists`**
- List the user's existing playlists
- Parameters: `limit` (int, default 20, max 50)
- Returns: list with `id`, `name`, `track_count`, `description`, `spotify_url`

**`spotify_reorder_tracks`**
- Move a track to a different position in a playlist
- Parameters: `playlist_id`, `range_start` (int), `insert_before` (int)
- Useful for arranging historical playlists in chronological order

### Library Tools (`tools/library.py`)

**`spotify_get_playlist_tracks`**
- Get all tracks currently in a playlist
- Parameters: `playlist_id` (string)
- Returns: ordered list of tracks with full details

---

## Error Handling Requirements

Every tool must handle these gracefully with clear, actionable error messages:

- **Track not found**: "No results found for '[query]'. Try searching with just
  the artist name, or check for alternate titles."
- **Authentication failure**: "Spotify authentication failed. Run
  `python setup/get_refresh_token.py` to refresh your credentials."
- **Rate limiting**: Automatically retry with exponential backoff (max 3 retries)
- **Invalid playlist ID**: "Playlist not found. Use spotify_get_user_playlists
  to find valid playlist IDs."
- **Network timeout**: Retry once, then return a clear error message

---

## The Setup Script (`setup/get_refresh_token.py`)

This is a one-time script the user runs to get their Spotify refresh token.

It must:
1. Read `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from environment variables
   (and print a helpful error if they're missing, with instructions)
2. Start a temporary local HTTP server on port 8888
3. Open the user's browser to Spotify's authorization page
4. Catch the OAuth callback and exchange the code for tokens
5. Print the refresh token clearly to the terminal with copy-paste instructions
6. Optionally write a `.env` file template the user can fill in

---

## The Validation Script (`setup/check_setup.py`)

Checks everything is working before the user tries to use it in Claude Desktop:

1. Verifies all three environment variables are set
2. Attempts to authenticate with Spotify
3. Fetches the user's display name to confirm auth works
4. Prints a success message: "✅ SpotifyMCP is ready. Connected as: [username]"
5. Or prints specific failure messages for each possible problem

---

## Claude Desktop Configuration

After building the server, create the Claude Desktop config entry. The config file
locations are:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

The entry to add:

```json
{
  "mcpServers": {
    "SpotifyMCP": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/SpotifyMCP/server.py"],
      "env": {
        "SPOTIFY_CLIENT_ID": "PASTE_YOUR_CLIENT_ID_HERE",
        "SPOTIFY_CLIENT_SECRET": "PASTE_YOUR_CLIENT_SECRET_HERE",
        "SPOTIFY_REFRESH_TOKEN": "PASTE_YOUR_REFRESH_TOKEN_HERE"
      }
    }
  }
}
```

**Automatically update this file** with the correct absolute path to `server.py`
based on where the project is built. Leave the credential values as placeholders
for the user to fill in.

---

## README.md Requirements

Write a clear README that covers:

### One-Time Setup (5 steps)
1. **Create a Spotify Developer App**
   - Go to developer.spotify.com/dashboard
   - Create app, set redirect URI to `http://localhost:8888/callback`
   - Copy Client ID and Client Secret

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```
   export SPOTIFY_CLIENT_ID=your_id_here
   export SPOTIFY_CLIENT_SECRET=your_secret_here
   ```

4. **Get your refresh token**
   ```
   python setup/get_refresh_token.py
   ```
   Browser opens → click Allow → copy the token printed in terminal

5. **Verify everything works**
   ```
   python setup/check_setup.py
   ```

6. **Add to Claude Desktop config** (instructions with exact file path)

7. **Restart Claude Desktop**

### Example Prompts for Claude
Include these example conversations so the user knows what to ask:

- "Make me a playlist that traces the history of House of the Rising Sun,
   from the earliest folk recordings through The Animals and beyond"
- "I want to listen to Richard Strauss's Salome — which recording on Spotify
   is considered the best? Add it to a new playlist called 'Strauss Operas'"
- "Create a late-night jazz playlist, around 90 minutes, atmospheric and slow"
- "Find me an EDM version of a 1960s protest song — something with weight to it"
- "I like Radiohead and Nick Cave — build me a playlist in that vibe with 12 songs"

---

## Important Notes for Implementation

1. **Use `python -m venv venv` only if asked** — keep setup simple by default,
   using the system Python

2. **The server must use stdio transport** (not HTTP) — this is what Claude
   Desktop's MCP integration expects

3. **Test that `python server.py` starts without errors** before finishing

4. **All tools must include helpful descriptions** — these descriptions are what
   Claude reads to decide which tool to use, so make them clear and specific

5. **Handle the "Stroll On" problem** — document in tool descriptions that
   Claude should search by both original title AND known alternate titles before
   concluding a track isn't on Spotify

6. **Spotipy handles token refresh automatically** when initialized with a
   `SpotifyOAuth` cache handler — use this rather than manual token management
