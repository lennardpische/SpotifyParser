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

### Phase 1 — Sentence-transformer embeddings (works now)
Embed every track in `my_tracks.csv` using `track_name + artist + album` with a model like `all-MiniLM-L6-v2` (`sentence-transformers` library). At inference time, embed the most recently played tracks from `listening_history.json` and retrieve nearest neighbors by cosine similarity. No extra Spotify API calls needed at inference.

### Phase 2 — Audio features as enriched input
Call [Get Track's Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features) for all tracks in `my_tracks.csv` to get `energy`, `valence`, `tempo`, `danceability`, etc. Concatenate these feature vectors with the text embeddings from Phase 1 for richer similarity, or train a small feedforward net to learn a personal preference score per track.

### Phase 3 — Sequential transformer / next-track prediction (needs accumulated history)
Treat `listening_history.json` ordered by `played_at` as a token sequence and train a transformer-based next-item model (e.g. BERT4Rec or a small GPT-style model in PyTorch). 50 tracks is too little data — run the script regularly to build up history first. This mirrors how Spotify's own rec engine works and is the highest-ceiling approach.
