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

### 3. Set environment variables

**Mac/Linux:**
```bash
export SPOTIFY_CLIENT_ID=your_client_id_here
export SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

**Windows (Command Prompt):**
```cmd
set SPOTIFY_CLIENT_ID=your_client_id_here
set SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Get your refresh token

```
python setup/get_refresh_token.py
```

A browser window will open asking you to authorize the app. Click **Allow**.
Your refresh token will be printed in the terminal — copy it.

### 5. Verify everything works

```
python setup/check_setup.py
```

You should see: `✅ SpotifyMCP is ready. Connected as: [your username]`

### 6. Add to Claude Desktop config

Open your Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this inside the `"mcpServers"` object (create the object if it doesn't exist):

```json
{
  "mcpServers": {
    "SpotifyMCP": {
      "command": "python",
      "args": ["C:\\Users\\Daddy\\Apps\\SpotifyMCP\\server.py"],
      "env": {
        "SPOTIFY_CLIENT_ID": "PASTE_YOUR_CLIENT_ID_HERE",
        "SPOTIFY_CLIENT_SECRET": "PASTE_YOUR_CLIENT_SECRET_HERE",
        "SPOTIFY_REFRESH_TOKEN": "PASTE_YOUR_REFRESH_TOKEN_HERE"
      }
    }
  }
}
```

Replace the three placeholder values with your actual credentials.

### 7. Restart Claude Desktop

Quit and reopen Claude Desktop. The SpotifyMCP tools will be available in your
next conversation.

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

**"Spotify authentication failed"** — Run `python setup/get_refresh_token.py` again.
Refresh tokens can expire if unused for a long time or if you revoke app access.

**Track not found** — Ask Claude to search for alternate titles. Some tracks appear
under different names (e.g., "Stroll On" instead of "Train Kept A-Rollin'").

**Server doesn't start** — Make sure `pip install -r requirements.txt` completed
successfully, and that you're using Python 3.10+.
