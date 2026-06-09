# SpotifyMCP — Auth Redesign

## Context

SpotifyMCP is a working Python MCP server built with FastMCP and Spotipy.
The server starts correctly and all 8 tools are functional. The only problem
is authentication — credentials are not reliably reaching the server when
launched by Claude Desktop.

Do NOT rebuild the server from scratch. Read the existing code first,
understand what's there, then make targeted fixes.

---

## The Problem

The current auth flow has three issues:

1. **Credentials are stored in Claude Desktop's config file** as environment
   variables. On some Windows systems these are not reliably passed to the
   server subprocess. This is the root cause of the "Spotify authentication
   failed" errors.

2. **`open_browser=False` may not be set** in the SpotifyOAuth call in
   `spotify_client.py`. In a headless subprocess, if Spotipy ever attempts
   a browser fallback it fails silently. Verify this is set and fix it if not.

3. **There is no self-healing auth** — when credentials are wrong or missing,
   the server throws a raw error instead of guiding the user to fix it from
   inside the chat window.

---

## The Fix

### Step 1 — New credentials file

Create the directory `C:\Users\Daddy\.keys\` if it doesn't exist.

The server should load credentials in this priority order:
1. Environment variables (keep this as a fallback for compatibility)
2. `C:\Users\Daddy\.keys\spotify.json`

The credentials file format:
```json
{
  "SPOTIFY_CLIENT_ID": "your_client_id_here",
  "SPOTIFY_CLIENT_SECRET": "your_client_secret_here",
  "SPOTIFY_REFRESH_TOKEN": "your_refresh_token_here"
}
```

If the file exists but is missing some values, use what's there and fall
back to environment variables for the rest.

### Step 2 — Migrate existing credentials

Read the current credentials from `%APPDATA%\Claude\claude_desktop_config.json`
(look inside the SpotifyMCP env block). Write them to
`C:\Users\Daddy\.keys\spotify.json` in the JSON format above. Do NOT remove
them from the config file yet — keep both in sync for now.

### Step 3 — Add a `spotify_setup` MCP tool

This tool handles the full OAuth flow from inside the Claude chat window.
The user should never need to open a terminal for auth.

Behavior:
1. Check what credentials are already in the `.keys` file
2. If `SPOTIFY_CLIENT_ID` or `SPOTIFY_CLIENT_SECRET` are missing, return a
   message asking the user to paste them:
   ```
   SpotifyMCP needs your Spotify app credentials to get started.
   Please paste your Client ID:
   ```
   Accept the values as tool parameters: `client_id` and `client_secret`
   (both optional strings — if not provided, prompt for them)
3. Once Client ID and Client Secret are available, open the browser to
   Spotify's OAuth authorization URL with these scopes:
   - playlist-read-private
   - playlist-modify-public
   - playlist-modify-private
4. Start a local HTTP server on port 8888 to catch the OAuth callback
5. Exchange the authorization code for tokens automatically
6. Save all three values to `C:\Users\Daddy\.keys\spotify.json` in JSON format
7. Reload the credentials into the running server without requiring a restart
8. Return: "✅ Spotify connected successfully as [username]. You're ready
   to create playlists."

Tool signature:
```python
@mcp.tool()
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
```

### Step 4 — Self-healing error handling

In `spotify_client.py`, wrap all API calls so that a 401/auth error returns
a friendly message instead of a raw exception:

```
Spotify authentication failed. Call the spotify_setup tool to fix this —
no terminal required.
```

### Step 5 — Update Claude Desktop config

Update `%APPDATA%\Claude\claude_desktop_config.json` to remove the credential
env vars from the SpotifyMCP entry (since they now live in the .keys file).
The entry should simplify to:

```json
"SpotifyMCP": {
  "command": "python",
  "args": ["C:\\Users\\Daddy\\Apps\\SpotifyMCP\\server.py"]
}
```

---

## Testing

After making all changes, test in this order:

1. Run `python server.py` — confirm it starts cleanly
2. Run `python setup/check_setup.py` — confirm it reads from the .keys file
   and shows "✅ Connected as: [username]"
3. Confirm `C:\Users\Daddy\.keys\spotify.json` exists and has all 3 values
4. Confirm `%APPDATA%\Claude\claude_desktop_config.json` is valid JSON
   after your edits (use `python -m json.tool` to validate)
5. Print "All tests passed — restart Claude Desktop to apply changes"

---

## What NOT to change

- Do not rewrite or restructure the existing tools
- Do not change `requirements.txt` unless a new package is needed
- Do not rename any files
- Do not change the FastMCP server name or tool names
- The 8 existing tools are working correctly — leave them alone
