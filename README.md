# SpotifyParser

## What this is

🎵 A small Python app that pulls my Spotify data (playlists, liked songs, recently played) into JSON and a growing listening-history so I can build personalized recs later.

- **Playlists** — names, IDs, track counts → `my_playlists.csv`
- **Library (playlists + liked)** — playlist tracks + liked songs only → `my_tracks.csv`
- **Listening history** — accumulated recently played (distinct by track, new songs merged in) → `listening_history.json`

Auth is via Spotify OAuth Web API (incognito browser)
Secrets live in `.env`. Run `python3 src/parser.py` to refresh playlists, liked, and recently played and append new recent plays to the history.

---

## Next steps

- **Seed-based recs:** I'll use `my_tracks.csv` / `listening_history.json` `track_id` (and optionally artist) with [Spotify Get Recommendations](https://developer.spotify.com/documentation/web-api/reference/get-recommendations). 
- **Audio features:** I'll call [Get Track's Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features) for my tracks and use the features as extra seeds or for similarity. (most likely option)
- **NLP / embeddings:** I'll run sentence-transformers (e.g. `all-MiniLM-L6-v2`) on `track_name` + `artist` + `album` and use cosine similarity or k-NN for "similar tracks" in my data.
- **Sequence / transformer:** I'll treat listening order (e.g. `played_at`) as a sequence, train a next-track or next-embedding model (PyTorch), and use predictions with Spotify's API or a lookup.
