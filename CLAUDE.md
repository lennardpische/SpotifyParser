# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python3 src/parser.py
```

This triggers a Spotify OAuth flow (opens an incognito browser window on macOS), then fetches playlists, liked songs, and recently played, writing output files to the project root.

## Environment setup

Copy `.env` and populate:
```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Dependencies: `spotipy`, `pandas`, `python-dotenv`. Install with `pip install spotipy pandas python-dotenv`.

The OAuth token cache is stored in `.cache` (gitignored). Delete it to force re-authentication.

## Architecture

All source is in `src/`. Modules are imported as flat names (no package), so `parser.py` inserts `src/` onto `sys.path` when run as a script.

- **`config.py`** — Loads `.env`, exposes `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, and `get_output_dir()` (project root). Called first by `parser.py` via `config.validate()`.
- **`auth.py`** — Patches `webbrowser.open` to open the OAuth URL in an incognito window (Chrome/Firefox on macOS), then returns a `spotipy.Spotify` client.
- **`playlists.py`** — Fetches all user playlists and saves `my_playlists.csv` (name, id, track count, sorted by count desc).
- **`tracks.py`** — Three fetchers: playlist tracks (via `sp._get` for pagination), liked songs, recently played. Manages a persistent `listening_history.json` deduped by `track_id` (newest `played_at` wins on collision). Also saves `last_recently_played.json` as a state file to detect when Spotify's 50-play window has rotated.
- **`parser.py`** — Orchestrates the above in order. The CSV `my_tracks.csv` contains only playlist + liked tracks (not recently played).

## Output files (all gitignored)

| File | Contents |
|---|---|
| `my_playlists.csv` | Playlist name, id, track count |
| `my_tracks.csv` | All playlist + liked tracks (track_name, artist, track_id, album, playlist_name, playlist_id) |
| `listening_history.json` | Accumulated recently played, deduped by track_id, newest first |
| `last_recently_played.json` | State snapshot used to detect rolling-window rotation |
