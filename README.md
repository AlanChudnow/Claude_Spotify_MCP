# SpotifyMCP

An MCP server that connects Claude Desktop to Spotify. Ask Claude to research,
curate, and create playlists directly in your Spotify account.

---

## One-Time Setup

### 1. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Set the **Redirect URI** to exactly: `http://127.0.0.1:8888/callback`
4. Copy your **Client ID** and **Client Secret**

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Add to Claude Desktop config

Open your Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this inside the `"mcpServers"` object (create the object if it doesn't exist):

```json
{
  "mcpServers": {
    "SpotifyMCP": {
      "command": "python",
      "args": ["C:\\Users\\Daddy\\Apps\\SpotifyMCP\\server.py"]
    }
  }
}
```

### 4. Restart Claude Desktop

Quit and reopen Claude Desktop.

### 5. Run first-time auth from inside Claude

In a new conversation, call the setup tool with your app credentials:

```
spotify_setup(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET")
```

A browser window will open asking you to authorize the app. Click **Allow**.
SpotifyMCP will catch the callback automatically, save your credentials, and
confirm with: `✅ Spotify connected successfully as [your username].`

You never need to do this again — credentials are saved to
`C:\Users\Daddy\.keys\spotify.json` and loaded automatically on every start.

---

## How Credentials Work

Credentials are stored in `C:\Users\Daddy\.keys\spotify.json` in this format:

```json
{
  "SpotifyKeys": {
    "SpotifyMCP": {
      "SPOTIFY_CLIENT_ID": "your_client_id",
      "SPOTIFY_CLIENT_SECRET": "your_client_secret",
      "SPOTIFY_REFRESH_TOKEN": "your_refresh_token"
    }
  }
}
```

The server loads credentials in this priority order:
1. `C:\Users\Daddy\.keys\spotify.json` *(takes priority)*
2. Environment variables `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
   `SPOTIFY_REFRESH_TOKEN` *(fallback)*

You do not need to put credentials in the Claude Desktop config file.
Token refresh is handled automatically and silently — you will never be
asked to re-authenticate during normal use.

---

## Example Prompts

Once configured, try asking Claude:

- *"Make me a playlist that traces the history of 'House of the Rising Sun' —
  from the earliest folk recordings through The Animals and beyond"*

- *"I want to listen to Richard Strauss's Salome — which recording on Spotify
  is considered the best? Add it to a new playlist called 'Strauss Operas'"*

- *"Create a late-night jazz playlist, around 90 minutes, atmospheric and slow"*

- *"Find me an EDM version of a 1960s protest song — something with weight to it"*

- *"I like Radiohead and Nick Cave — build me a playlist in that vibe with 12 songs"*

- *"Create a playlist that tells the history of 'Train Kept A-Rollin' — start with
  Tiny Bradshaw's 1951 original, through Johnny Burnette's rockabilly version, the
  Yardbirds with Jeff Beck, then the rare Beck + Page version called 'Stroll On'
  from the film Blow Up, then Aerosmith, then Motörhead"*

Claude will research the tracks (including alternate titles like "Stroll On"),
present them for your approval, then create the playlist when you say
**"put this in Spotify"**.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `spotify_setup` | Set up or repair authentication from inside Claude — no terminal needed |
| `spotify_search_tracks` | Search by title, artist, album, year — supports advanced operators |
| `spotify_search_album` | Find a specific album and its full track listing |
| `spotify_find_track` | Smart single-track lookup with alternate title handling |
| `spotify_create_playlist` | Create a new empty playlist |
| `spotify_add_tracks` | Add tracks to an existing playlist |
| `spotify_create_playlist_with_tracks` | Create playlist + add tracks in one call |
| `spotify_get_user_playlists` | List your existing playlists |
| `spotify_reorder_tracks` | Move tracks to different positions |
| `spotify_get_playlist_tracks` | Get all tracks in a playlist |

---

## Troubleshooting

**"Spotify authentication failed"** — Call the `spotify_setup` tool from inside
Claude. No terminal required. If you've revoked app access or the refresh token
has expired, `spotify_setup` will walk you through re-authorizing.

**Track not found** — Ask Claude to search for alternate titles. Some tracks appear
under different names (e.g., "Stroll On" instead of "Train Kept A-Rollin'").

**Server doesn't start** — Make sure `pip install -r requirements.txt` completed
successfully, and that you're using Python 3.10+.

**Credentials not loading** — Confirm `C:\Users\Daddy\.keys\spotify.json` exists
and contains all three keys (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
`SPOTIFY_REFRESH_TOKEN`) nested under `SpotifyKeys.SpotifyMCP`. Running
`spotify_setup` again will recreate this file correctly.
