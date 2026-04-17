# SpotifyParser

A personal tool that accumulates your Spotify listening history and generates music recommendations — built because Spotify's own suggestions stopped being useful, and because the data to do better was sitting right there in their API.

**Status: finally complete.**

---

## The problem

Spotify's recommendation engine is a black box. You go through a phase where you're obsessively listening to one kind of music, and it still serves you the same playlist it would have six months ago. The data to do better exists — Spotify computes audio features (energy, tempo, mood, danceability) for every track in their catalog — but accessing it turned into a problem mid-project.

---

## The API situation (why the pivot happened)

The original plan was to blend two signals: text similarity (what the song is called, who made it) and audio features (what it actually sounds like). That combination would have been much more accurate — two tracks by the same artist can sound completely different, and text alone can't tell them apart.

In late 2024, Spotify moved the `audio-features` endpoint behind "Extended Quota Mode" — a manual approval process requiring a commercial use case. Individual developers can't get through it. The endpoint still exists, it just returns a 403 for any new app. Same story for their `recommendations` endpoint.

So the project pivoted to text-only similarity, using Spotify's artist catalog browsing (which is still open) as the source of new tracks to evaluate. It's a meaningful limitation, but the pipeline still works — it just can't hear the music, only read its label.

---

## How it works

**Step 1 — Build listening history**

Every time the script runs, it pulls your last 50 recently played tracks from Spotify and merges them into a local `listening_history.json`, deduped by track ID. This is necessary because Spotify only exposes a rolling window of 50 plays — run the script often enough and you accumulate a real picture of what you've been listening to.

**Step 2 — Fetch new tracks to evaluate**

The script takes your 5 most recently played artists and browses their catalogs on Spotify — albums, singles, deep cuts. It pulls up to 100 tracks from those catalogs that you haven't heard before (anything already in your history is filtered out before it even enters the pool).

**Step 3 — Rank by text similarity**

Each track — both the ones you've recently played and the new candidates — gets converted into a short text string: `"track name · artist · album"`. These strings are fed into a pre-trained sentence embedding model (`all-MiniLM-L6-v2` from HuggingFace), which turns each one into a vector of numbers that captures something about the meaning and context of the words.

Your 5 most recent plays become a query: their vectors are averaged into a single point in that space. Every candidate track gets a similarity score based on how close it sits to that point. The top 5 are your recommendations.

**Step 4 — Persist and deduplicate**

Recommended tracks are saved to `recommended_history.json` so they never come up again. Tracks you explicitly dismiss via `dismiss.py` go into `dismissed.json` and are also permanently excluded.

---

## What "text similarity" actually means here

The model doesn't know what a song sounds like. It was trained on large amounts of text and learned that certain words and phrases tend to appear in similar contexts. So "Radiohead · OK Computer" and "Thom Yorke · The Eraser" end up close together in its vector space — not because it knows they sound alike, but because it's seen those names discussed in similar contexts across the internet.

This means the recommendations pick up on artist identity, scene, era, and genre naming conventions — but not timbre, tempo, or mood. A quiet acoustic track and a loud electric one by the same artist look identical to this model. That's the ceiling of the text-only approach, and it's where the audio features would have closed the gap.

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

Opens an incognito browser for Spotify OAuth, then fetches your data and writes output files to the project root. Re-run any time to pull new plays and refresh recommendations.

**5. Run automatically every 12 hours (macOS)**

A LaunchAgent is included. Load it once:

```bash
launchctl load ~/Library/LaunchAgents/com.spotifyparser.plist
```

> Note: (MAC users) the agent needs Full Disk Access to run if the project lives on `~/Desktop`. Grant it in System Settings → Privacy & Security → Full Disk Access, or move the project to `~/Documents`.

To stop it:

```bash
./stop_parser.sh
```

Logs go to `launchd_stdout.log` and `launchd_stderr.log` in the project root. If your Spotify token expires, a macOS notification fires telling you to re-authenticate manually.

**6. Review and dismiss recommendations**

```bash
python3 src/dismiss.py
```

Shows your current recommendations one at a time. `d` to dismiss, Enter to keep, `q` to quit. Dismissed tracks are saved to `dismissed.json` and never surface again.

---

## Output files

| File | Contents |
|---|---|
| `listening_history.json` | Accumulated recently played, deduped by track ID, newest first |
| `last_recently_played.json` | Snapshot used to detect when Spotify's 50-play window rotates |
| `discovered_tracks.json` | New candidate tracks from your seed artists' catalogs, fetched each run |
| `recommendations.csv` | Top 5 recommended tracks with similarity score |
| `recommended_history.json` | All track IDs ever recommended — delete to reset |
| `dismissed.json` | Tracks explicitly dismissed — permanently excluded |

All output files are gitignored.

---

## Architecture

```
src/
  config.py          — loads .env, exposes credentials and output path
  auth.py            — OAuth flow, opens incognito browser on macOS
  tracks.py          — fetches recently played + discovery tracks, manages history JSON
  recommendations.py — text embeddings over discovery pool → recommendations.csv
  parser.py          — orchestrates everything in order
  dismiss.py         — interactive CLI to dismiss unwanted recommendations
```

---

## Limitations

- **50-play window**: Spotify only exposes the last 50 recently played tracks. Run the script frequently enough that the window doesn't rotate without you capturing it — a warning prints if it has.
- **Text-only signal**: recommendations reflect artist/album/title similarity, not sonic similarity. Two very different-sounding tracks by the same artist are indistinguishable to this model.
- **Candidate pool size**: capped at 100 tracks per run, sourced only from your 5 most recent seed artists. The pool is only as diverse as your recent listening.
- **`recommended_history.json` grows indefinitely**: the pool of unseen candidates shrinks over time. Delete the file to start fresh.
