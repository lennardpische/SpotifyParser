# Architecture

### `config.py`
Loads `.env` from the project root and exposes three credentials (`CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`) as module-level constants. Also provides `get_output_dir()` which returns the project root as the directory where all output files are written. `validate()` exits early with a clear error if credentials are missing — called first in `parser.py` so nothing runs without a valid environment.

---

### `auth.py`
Handles Spotify OAuth. Patches `webbrowser.open` so the auth URL opens in an incognito/private window (tries Chrome, then Chromium, then Firefox on macOS). Returns an authenticated `spotipy.Spotify` client with the scopes needed for recently played and user profile. The OAuth token is cached in `.cache` at the project root — delete it to force re-authentication.

---

### `tracks.py`
Handles everything related to recently played tracks. `fetch_recently_played` pulls the last 50 plays from `current_user_recently_played`. `merge_recently_played_into_history` loads the existing `listening_history.json`, merges in new plays (deduped by `track_id`, newest `played_at` wins on collision), and saves back to disk — this is how history accumulates across runs since Spotify only exposes a rolling 50-play window. `warn_if_new_recently_played_list` saves a signature of the current 50 plays and warns if the window has rotated to a completely new set since the last run.

---

### `recommendations.py`
Loads the full listening history from `listening_history.json`. Uses the 5 most recent tracks as the query and the rest as the candidate pool. Converts each track to a short text string (`"track_name artist album"`), encodes everything using the `all-MiniLM-L6-v2` sentence-transformer model, averages the recent embeddings into a single query vector, and ranks candidates by cosine similarity. Returns the top 20 matches. Saves to `recommendations.csv` with a `similarity_score` column.

---

### `parser.py`
The entry point. Runs everything in order:
1. Validates config
2. Authenticates
3. Fetches recently played and merges into listening history
4. Generates and saves recommendations
