"""
SpotifyMCP — MCP server entry point.
Connects Claude Desktop to Spotify via the Model Context Protocol.
Uses stdio transport as required by Claude Desktop's MCP integration.
"""

from fastmcp import FastMCP

from tools.search import (
    spotify_search_tracks,
    spotify_search_album,
    spotify_find_track,
)
from tools.playlists import (
    spotify_create_playlist,
    spotify_add_tracks,
    spotify_create_playlist_with_tracks,
    spotify_get_user_playlists,
    spotify_reorder_tracks,
)
from tools.library import spotify_get_playlist_tracks
from tools.auth import spotify_setup

mcp = FastMCP("SpotifyMCP")

# Register all tools
mcp.tool()(spotify_search_tracks)
mcp.tool()(spotify_search_album)
mcp.tool()(spotify_find_track)
mcp.tool()(spotify_create_playlist)
mcp.tool()(spotify_add_tracks)
mcp.tool()(spotify_create_playlist_with_tracks)
mcp.tool()(spotify_get_user_playlists)
mcp.tool()(spotify_reorder_tracks)
mcp.tool()(spotify_get_playlist_tracks)
mcp.tool()(spotify_setup)

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        from setup.test_mcp import run_tests
        run_tests()
    else:
        mcp.run()
