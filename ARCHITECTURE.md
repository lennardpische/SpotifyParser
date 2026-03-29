# Architecture

### `config.py`
Loads `.env` from the project root and exposes three credentials (`CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`) as module-level constants. Also provides `get_output_dir()` which returns the project root as the directory where all output files are written. `validate()` exits early with a clear error if credentials are missing — called first in `parser.py` so nothing runs without a valid environment.

---

### `auth.py`
Handles Spotify OAuth. Patches `webbrowser.open` so the auth URL opens in an incognito/private window (tries Chrome, then Chromium, then Firefox on macOS). Returns an authenticated `spotipy.Spotify` client with the scopes needed for playlists, liked songs, recently played, and user profile. The OAuth token is cached in `.cache` at the project root — delete it to force re-authentication.

---

### `playlists.py`
Fetches all of the user's playlists (including collaborative ones) using `sp.current_user_playlists` with pagination. Returns a list of dicts with `name`, `id`, and `tracks` (count). Saves to `my_playlists.csv`, sorted by track count descending.

---

### `tracks.py`
The heaviest module. Four main responsibilities:

**Fetching** — three fetchers: `fetch_playlist_tracks` (paginates through every playlist using `sp._get`), `fetch_liked_tracks` (paginates `current_user_saved_tracks`), and `fetch_recently_played` (last 50 plays via `current_user_recently_played`). All three return the same shape of dict: `track_name`, `artist`, `track_id`, `album`, `playlist_name`, `playlist_id`, `played_at`.

**Listening history** — `merge_recently_played_into_history` loads the existing `listening_history.json`, merges in new plays (deduped by `track_id`, newest `played_at` wins on collision), and saves back to disk. This accumulates over time since Spotify only exposes a rolling 50-play window.

**Rotation detection** — `warn_if_new_recently_played_list` saves a signature of the current 50 plays and warns if the window has rotated to a completely new set since the last run.

**CSV export** — `save_tracks_csv` writes `my_tracks.csv` from playlists + liked songs only (recently played is kept separate in the JSON history).

---

### `recommendations.py`
Loads the library from `my_tracks.csv` and the N most recent tracks from `listening_history.json`. Converts each track to a short text string (`"track_name artist album"`), encodes everything using the `all-MiniLM-L6-v2` sentence-transformer model, averages the recent track embeddings into a single query vector, and ranks the library by cosine similarity. Returns the top 20 matches that aren't already in the recent tracks. Saves to `recommendations.csv` with a `similarity_score` column.

---

### `parser.py`
The entry point. Runs everything in order:
1. Validates config
2. Authenticates
3. Fetches + saves playlists
4. Fetches playlist tracks, liked songs, and recently played
5. Merges recently played into listening history
6. Saves library CSV
7. Generates and saves recommendations
