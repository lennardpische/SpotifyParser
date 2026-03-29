"""Recommendations: sentence-transformer text embeddings over the library,
queried by the most recently played tracks in listening_history.json."""
import os
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

import config

MODEL_NAME = "all-MiniLM-L6-v2"
RECS_FILE = "recommendations.csv"
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


def generate_recommendations(out_dir=None):
    """Embed listening history; use most recent N tracks as query; return top N_RECS similar tracks."""
    out_dir = out_dir or config.get_output_dir()

    history = _load_history(out_dir)
    if len(history) < N_RECENT + 1:
        print("    ⚠️ Not enough listening history yet — keep running the script to accumulate data.")
        return []

    recent = history[:N_RECENT]
    library = history[N_RECENT:]  # everything older than the query window

    print(f"    Loading model '{MODEL_NAME}' ...")
    model = SentenceTransformer(MODEL_NAME)

    library_texts = [_track_text(t) for t in library]
    recent_texts = [_track_text(t) for t in recent]
    recent_ids = {t.get("track_id") for t in recent}

    print(f"    Embedding {len(library_texts)} library tracks ...")
    library_emb = model.encode(library_texts, convert_to_tensor=True, show_progress_bar=False)

    print(f"    Embedding {len(recent_texts)} recent tracks as query ...")
    recent_emb = model.encode(recent_texts, convert_to_tensor=True, show_progress_bar=False)

    query = recent_emb.mean(dim=0, keepdim=True)
    scores = util.cos_sim(query, library_emb)[0].cpu().numpy()

    ranked = sorted(
        [(float(score), track) for score, track in zip(scores, library)
         if track.get("track_id") not in recent_ids],
        key=lambda x: x[0],
        reverse=True,
    )

    recs = []
    seen_ids = set()
    for score, track in ranked:
        tid = track.get("track_id")
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        recs.append({**track, "similarity_score": round(score, 4)})
        if len(recs) >= N_RECS:
            break

    return recs


def save_recommendations(recs, out_dir=None):
    """Save recommendations to recommendations.csv. Returns path or None."""
    out_dir = out_dir or config.get_output_dir()
    if not recs:
        return None
    path = os.path.abspath(os.path.join(out_dir, RECS_FILE))
    pd.DataFrame(recs).to_csv(path, index=False)
    return path
