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

Each track in the listening history is converted to a short text string — `"track name artist album"` — and embedded into a vector using `sentence-transformers` with the `all-MiniLM-L6-v2` model. The 5 most recently played songs become a query; the script finds the closest matches in the rest of the accumulated history.

It works well for surfacing tracks from your past that fit the current mood. It's less good at capturing raw sound — a quiet acoustic track and a loud electric one by the same artist look identical to this model.

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

**5. Run automatically every 12 hours (macOS)**

A LaunchAgent is included that runs the script silently in the background without any special permissions. Load it once:

```bash
launchctl load ~/Library/LaunchAgents/com.spotifyparser.plist
```

To stop it:

```bash
./stop_parser.sh
```

Logs are written to `launchd_stdout.log` and `launchd_stderr.log` in the project root. If your Spotify token expires, a macOS notification will fire telling you to re-run the parser manually.

**6. Review and dismiss recommendations**

```bash
python3 src/dismiss.py
```

Shows your current recommendations one at a time. Press `d` to dismiss, Enter to keep, `q` to quit. Dismissed tracks are saved to `dismissed.json` and permanently excluded from future runs.

---

## Output files

| File | Contents |
|---|---|
| `listening_history.json` | Accumulated recently played, deduped by track, newest first |
| `last_recently_played.json` | State snapshot for detecting when Spotify's 50-play window rotates |
| `discovered_tracks.json` | Tracks from your seed artists' catalogs, fetched each run for discovery |
| `recommendations.csv` | Top 20 recommended tracks with similarity score and source (history/discovery) |
| `recommended_history.json` | All track IDs ever recommended — used to prevent repeats across runs. Delete to reset. |
| `dismissed.json` | Tracks you've explicitly dismissed — permanently excluded from recommendations |

All output files are gitignored.

---

## Architecture

```
src/
  config.py          — loads .env, exposes credentials and output path
  auth.py            — OAuth flow, opens incognito browser on macOS
  tracks.py          — fetches recently played and discovery tracks, manages history JSON files
  recommendations.py — text embeddings over history + discovery pool → recommendations.csv
  parser.py          — orchestrates everything in order
  dismiss.py         — interactive CLI to dismiss unwanted recommendations
```

The OAuth token is cached in `.cache` (gitignored). Delete it to force re-authentication.

### Recommendation pipeline

Each run:
1. Fetch the latest 50 recently played and merge into `listening_history.json`
2. Browse the catalogs of your 5 most recently played artists to build a discovery pool (`discovered_tracks.json`)
3. Embed all candidates (history + discovery, minus previously recommended and dismissed tracks) using `sentence-transformers`
4. Use your 5 most recent plays as a query vector; return the 20 closest matches
5. Persist recommended track IDs to `recommended_history.json` so they never repeat

---

## Limitations

- **50-play window**: Spotify only exposes the last 50 recently played tracks via the API. The script accumulates these over time, but you have to run it frequently enough that the window doesn't rotate without you capturing it. A warning prints if the window has rotated since the last run.
- **Library size**: The text embedding step runs locally on CPU. Large libraries (10k+ tracks) are slow but work fine.
- **API restrictions**: Spotify deprecated the audio features, recommendations, and related-artists endpoints for basic developer apps in late 2024. Discovery here is based on browsing seed artists' own catalogs, not Spotify's similarity graph.
- **`recommended_history.json` grows indefinitely**: over time the pool of unseen candidates shrinks. Delete the file to start fresh if recommendations run dry.
