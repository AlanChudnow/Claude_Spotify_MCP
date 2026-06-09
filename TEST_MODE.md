# SpotifyMCP — Add Test Mode

## Context

SpotifyMCP is a working Python MCP server built with FastMCP and Spotipy.
Read the existing code before making any changes. Do NOT rebuild anything
from scratch.

---

## What to Build

Add a self-contained test mode to SpotifyMCP that validates the full
authentication and playlist workflow automatically. The goal is that Claude
Code (or any developer) can run a single command and know with certainty
whether the MCP is working end to end — with no human intervention required.

---

## Implementation

### 1. Add `setup/test_mcp.py`

Create a standalone test script that:

1. **Tests credential loading**
   - Confirms `C:\Users\Daddy\.keys\spotify.json` exists and has all 3 keys
   - Confirms the SpotifyClient can be instantiated without errors
   - Prints: `✅ Credentials loaded from spotify.json`

2. **Tests Spotify authentication**
   - Calls `sp.current_user()` to verify the token works
   - Prints: `✅ Authenticated as: [display_name] ([email])`
   - If this fails, prints the exact error and stops — do not continue

3. **Tests track search**
   - Searches for `artist:Aerosmith Train Kept a Rollin`
   - Confirms at least 1 result is returned
   - Confirms the result has a valid `uri` field starting with `spotify:track:`
   - Prints: `✅ Search works — found: [track name]`

4. **Tests playlist creation**
   - Creates a playlist named `SpotifyMCP Test — [timestamp]`
   - Description: `Automated test playlist — safe to delete`
   - Confirms the response has a `playlist_id`
   - Prints: `✅ Playlist created: [name] (id: [playlist_id])`

5. **Tests adding tracks**
   - Adds this one track to the test playlist:
     `spotify:track:6zb4VGZE20uKHc0mydFgR5` (Aerosmith — Train Kept a Rollin')
   - Confirms `tracks_added == 1`
   - Prints: `✅ Track added successfully`

6. **Tests reading the playlist back**
   - Calls `get_playlist_tracks(playlist_id)`
   - Confirms exactly 1 track is returned
   - Confirms the track name contains "Train"
   - Prints: `✅ Playlist readback confirmed: [track name]`

7. **Cleans up**
   - Deletes the test playlist using the Spotify API directly:
     `sp.current_user_unfollow_playlist(playlist_id)`
   - Prints: `✅ Test playlist deleted`

8. **Final summary**
   - If all 7 steps passed: print `\n🎉 ALL TESTS PASSED — SpotifyMCP is
     fully operational\n`
   - If any step failed: print `\n❌ TESTS FAILED at step [N]: [error]\n`
   - Exit with code 0 on success, 1 on failure

### 2. Add a `--test` flag to `server.py`

So Claude Code can trigger the test without running a separate file:

```
python server.py --test
```

This should import and run `setup/test_mcp.py` directly, then exit.
If the flag is not present, the server starts normally as before.

### 3. Update `setup/check_setup.py`

At the end of the existing checks, add:

```
Run 'python server.py --test' for a full end-to-end playlist test.
```

---

## Run the Tests

After implementing, run the full test suite immediately:

```
python server.py --test
```

Fix any failures before finishing. The goal is a clean run that ends with:

```
🎉 ALL TESTS PASSED — SpotifyMCP is fully operational
```

Post the full test output so the results are visible.

---

## What NOT to change

- Do not modify any existing tools
- Do not change how the server starts in normal mode
- Do not change the credentials loading logic
- Do not leave test playlists in the user's Spotify account
