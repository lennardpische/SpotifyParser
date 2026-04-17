# SpotifyParser

![Project Status: Completed](https://img.shields.io/badge/Status-Completed-success) ![Python](https://img.shields.io/badge/Made%20with-Python-blue)

A personal tool that accumulates your Spotify listening history and surfaces new music you haven't heard — built after Spotify restricted access to their audio features API mid-project, forcing a pivot to text-based similarity.

> **Note on the API pivot:**
> The original plan used Spotify's `audio-features` endpoint to match songs by how they actually sound (tempo, energy, mood). In late 2024, Spotify locked that endpoint behind a commercial approval process that individual developers can't access. The project pivoted to text similarity using a pre-trained sentence embedding model — matching songs by name, artist, and album context rather than sonic properties.
>
> **See [`README_TECHNICAL.md`](README_TECHNICAL.md) for the full pipeline, setup instructions, and architecture.**

---

## What it does

Every 12 hours, the script:

1. Pulls your 50 most recently played tracks from Spotify and saves them locally
2. Browses the catalogs of your 5 most recent artists for up to 100 tracks you've never heard
3. Embeds all track names through a sentence transformer model (`all-MiniLM-L6-v2`)
4. Ranks the new candidates by similarity to your 5 most recent plays
5. Outputs your top 5 recommendations to `recommendations.csv`

Tracks you've already heard, been recommended before, or explicitly dismissed are permanently excluded.

---

## Quick start

```bash
pip install spotipy pandas python-dotenv sentence-transformers
cp .env.example .env  # fill in your Spotify app credentials
python3 src/parser.py
```