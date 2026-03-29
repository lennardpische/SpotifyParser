# SpotifyParser

A personal tool for pulling Spotify data and generating music recommendations, built because the DJ was not the best at performing that task.

---

## The problem

Spotify's recommendations are a black box. You hear a song you love, add it to a playlist, and the app's suggestions still feel generic. There's only one way to ask it "find me more songs that sound like what I've been playing this week," but its recommendations are often terrible... though the data is there!
Spotify computes audio features (energy, tempo, mood) for every track, but it's locked behind an API that's become increasingly hard to access.

This project is my attempt to own that data myself and build something on top of it.

---

## The API situation

Spotify's Web API used to be wide open, but in late 2024, Spotify started restricting access. The `audio-features` endpoint (and several others) were moved behind an approval wall. New apps couldn't use them without manually applying for "Extended Quota Mode," a process that requires submitting a description, a demo, and waiting on a review that often just doesn't come.

This effectively killed most hobby projects that relied on that data. The endpoint still exists, but hitting it with a new app ID returns a 403. Individual developer accounts can't apply for Extended Quota Mode at all, as it's gated behind a review process that requires a commercial use case. So Phase 2 as originally designed (blending audio features with text similarity) isn't possible without a different data source for the acoustic properties.

---

## How SpotifyParser works

There are three phases, each building on the last.

### Phase 1 — Text similarity (done)

The simplest version: treat each track as a short text string — `"track name artist album"` --> and find songs in your library that are semantically close to what you've been listening to recently.

This uses `sentence-transformers` with the `all-MiniLM-L6-v2` model, a small pre-trained language model that converts text into vectors. Tracks with similar names, artists, or albums end up close together in that vector space. Your 5 most recently played songs become a query and the script finds the closest matches in your library.

It works surprisingly well for finding more songs by the same artists or in the same genre cluster. It's less good at capturing *sound* (a quiet acoustic track and a loud electric one by the same artist look identical to this model, but we already explored why that is not fixable by individuals).

### Phase 2 — Audio features (blocked)

Spotify pre-computes numeric features for every track — energy, danceability, valence, acousticness, and more. The plan was to blend these with the text scores so recommendations reflect how a song actually sounds, not just what it's called.

That endpoint is behind Extended Quota Mode, which individual developers can't access. Blocked for now.

### Phase 3 — Sequence prediction (not yet)

The listening history is a sequence of songs, not just a set. There's information about what you play after what, how your taste shifts across a session. A small transformer trained on this sequence could learn to predict what comes next, closer to how Spotify's own system works internally.

This needs significantly more than 50 tracks of history to be useful. The script accumulates plays every time it runs, so this phase becomes viable over time.

---

## Setup

**1. Create a Spotify app**

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create an app, and set the redirect URI to `http://127.0.0.1:8888/callback`. Copy your client ID and secret.

**2. Configure environment**

```bash
cp .env.example .env
```

Fill in `.env`:
```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

**3. Install dependencies**

```bash
pip install spotipy pandas python-dotenv sentence-transformers
```

**4. Run**

```bash
python3 src/parser.py
```

This opens an incognito browser window for Spotify OAuth, then fetches your data and writes all output files to the project root. Re-run any time to add new recently played tracks to your history and refresh recommendations.

---

## Output files

| File | Contents |
|---|---|
| `my_playlists.csv` | All your playlists — name, ID, track count |
| `my_tracks.csv` | Every track from your playlists + liked songs |
| `listening_history.json` | Accumulated recently played, deduped by track, newest first |
| `last_recently_played.json` | State snapshot for detecting when Spotify's 50-play window rotates |
| `recommendations.csv` | Top 20 recommended tracks with similarity score |

All output files are gitignored.

---

## Architecture

```
src/
  config.py          — loads .env, exposes credentials and output path
  auth.py            — OAuth flow, opens incognito browser on macOS
  playlists.py       — fetches all playlists → my_playlists.csv
  tracks.py          — fetches playlist tracks, liked songs, recently played;
                       manages listening_history.json
  recommendations.py — text embeddings → recommendations.csv
  parser.py          — orchestrates everything in order
```

The OAuth token is cached in `.cache` (gitignored). Delete it to force re-authentication.

---

## Limitations

- **50-play window**: Spotify only exposes the last 50 recently played tracks via the API. The script accumulates these over time, but you have to run it frequently enough that the window doesn't rotate without you capturing it. A warning prints if the window has rotated since the last run.
- **Library size**: The text embedding step runs locally on CPU. Large libraries (10k+ tracks) are slow but work fine.
