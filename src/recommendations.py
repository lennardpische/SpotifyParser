"""Recommendations: sentence-transformer text embeddings over the library,
queried by the most recently played tracks in listening_history.json.

Pools both listening history and Spotify-discovered tracks as candidates.
Filters out previously recommended tracks and user-dismissed tracks.
"""
import os
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

import config
import tracks as tracks_module

MODEL_NAME = "all-MiniLM-L6-v2"
RECS_FILE = "recommendations.csv"
DISMISSED_FILE = "dismissed.json"
RECOMMENDED_HISTORY_FILE = "recommended_history.json"
N_RECENT = 5   # recent tracks used as the query
N_RECS = 20    # recommendations to return


def _track_text(row):
    return f"{row.get('track_name', '')} {row.get('artist', '')} {row.get('album', '')}".strip()


def _load_history(out_dir):
    """Load full listening history. Returns list of track dicts, newest first."""
    path = os.path.join(out_dir, "listening_history.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def _load_dismissed(out_dir):
    """Return set of track_ids the user has dismissed."""
    path = os.path.join(out_dir, DISMISSED_FILE)
    if not os.path.exists(path):
        return set()
    try:
        with open(path) as f:
            entries = json.load(f)
        return {e["track_id"] for e in entries if e.get("track_id")}
    except (json.JSONDecodeError, OSError):
        return set()


def _load_recommended_history(out_dir):
    """Return set of track_ids ever recommended in a previous run."""
    path = os.path.join(out_dir, RECOMMENDED_HISTORY_FILE)
    if not os.path.exists(path):
        return set()
    try:
        with open(path) as f:
            data = json.load(f)
        return set(data.get("track_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_recommended_history(new_ids, out_dir):
    """Union new_ids into the persistent recommended_history.json."""
    path = os.path.join(out_dir, RECOMMENDED_HISTORY_FILE)
    existing = _load_recommended_history(out_dir)
    updated = existing | set(new_ids)
    try:
        with open(path, "w") as f:
            json.dump({"track_ids": list(updated)}, f)
    except OSError:
        pass


def generate_recommendations(out_dir=None, discovered=None):
    """Embed candidate pool; use most recent N tracks as query; return top N_RECS.

    Candidate pool = listening history (minus recent query window)
                   + Spotify-discovered tracks (from discovered_tracks.json)
    Excludes tracks the user has dismissed or that were already recommended.
    """
    out_dir = out_dir or config.get_output_dir()

    history = _load_history(out_dir)
    if len(history) < N_RECENT + 1:
        print("    ⚠️ Not enough listening history yet — keep running the script to accumulate data.")
        return []

    dismissed = _load_dismissed(out_dir)
    prev_recommended = _load_recommended_history(out_dir)
    exclude_ids = dismissed | prev_recommended

    recent = history[:N_RECENT]
    recent_ids = {t.get("track_id") for t in recent}

    # Build candidate pool: history (older than query window) tagged as "history"
    history_pool = [{"source": "history", **t} for t in history[N_RECENT:]]

    # Discovery pool: tracks Spotify surfaced, tagged as "discovery"
    if discovered is None:
        discovered = tracks_module.load_discovered_tracks(out_dir)
    history_track_ids = {t.get("track_id") for t in history}
    discovery_pool = [
        {"source": "discovery", **t}
        for t in discovered
        if t.get("track_id") and t["track_id"] not in history_track_ids
    ]

    # Merge pools, dedup by track_id, filtering exclusions
    seen_pool_ids = set()
    pool = []
    for t in history_pool + discovery_pool:
        tid = t.get("track_id")
        if not tid or tid in seen_pool_ids or tid in recent_ids or tid in exclude_ids:
            continue
        seen_pool_ids.add(tid)
        pool.append(t)

    if not pool:
        print("    ⚠️ No candidates left after filtering dismissed/already-recommended tracks.")
        return []

    history_count = sum(1 for t in pool if t.get("source") == "history")
    discovery_count = sum(1 for t in pool if t.get("source") == "discovery")
    print(f"    Candidate pool: {history_count} from history, {discovery_count} from discovery")

    print(f"    Loading model '{MODEL_NAME}' ...")
    model = SentenceTransformer(MODEL_NAME)

    pool_texts = [_track_text(t) for t in pool]
    recent_texts = [_track_text(t) for t in recent]

    print(f"    Embedding {len(pool_texts)} candidate tracks ...")
    pool_emb = model.encode(pool_texts, convert_to_tensor=True, show_progress_bar=False)

    print(f"    Embedding {len(recent_texts)} recent tracks as query ...")
    recent_emb = model.encode(recent_texts, convert_to_tensor=True, show_progress_bar=False)

    query = recent_emb.mean(dim=0, keepdim=True)
    scores = util.cos_sim(query, pool_emb)[0].cpu().numpy()

    ranked = sorted(
        zip(scores, pool),
        key=lambda x: float(x[0]),
        reverse=True,
    )

    recs = []
    seen_ids = set()
    for score, track in ranked:
        tid = track.get("track_id")
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        recs.append({**track, "similarity_score": round(float(score), 4)})
        if len(recs) >= N_RECS:
            break

    return recs


def save_recommendations(recs, out_dir=None):
    """Save recommendations to recommendations.csv and record IDs so they won't repeat."""
    out_dir = out_dir or config.get_output_dir()
    if not recs:
        return None
    path = os.path.abspath(os.path.join(out_dir, RECS_FILE))
    pd.DataFrame(recs).to_csv(path, index=False)
    _save_recommended_history([r["track_id"] for r in recs if r.get("track_id")], out_dir)
    return path
