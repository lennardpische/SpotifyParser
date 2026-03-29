"""Spotify OAuth and client. Opens auth URL in incognito on macOS."""
import webbrowser
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config

#Opening the authentication URL in an incognito/private browser window
def _open_auth_url_incognito(url):
    """Open URL in an incognito/private browser window (macOS)."""
    print("--- Open this URL in an incognito/private window to log in ---")
    print(url)
    print("---")
    for app_name, flag in [
        ("Google Chrome", "--incognito"),
        ("Chromium", "--incognito"),
        ("Firefox", "-private-window"),
    ]:
        try:
            result = subprocess.run(
                ["open", "-na", app_name, "--args", flag, url],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print(f"--- Opened in {app_name} (incognito/private) ---")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    print("--- Opening in default browser (copy URL above into incognito if needed) ---")
    webbrowser.open(url)


# Patch webbrowser so Spotify auth opens in incognito
webbrowser.open = _open_auth_url_incognito

#Getting the Spotify client
def get_spotify_client():
    """Return an authenticated Spotipy client."""
    auth_manager = SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope="user-read-private user-read-recently-played",
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)
