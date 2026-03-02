"""Fetch user playlists and save summary to CSV."""
import os
import pandas as pd

import config


def fetch_playlists(sp):
    """Return list of dicts: name, id, tracks (count)."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        for item in results["items"]:
            track_count = 0
            if item:
                tracks_ref = item.get("tracks") or item.get("items")
                if isinstance(tracks_ref, dict) and "total" in tracks_ref:
                    track_count = tracks_ref["total"]
            if item:
                playlists.append({
                    "name": item.get("name", "Unknown Playlist"),
                    "id": item.get("id", "No ID"),
                    "tracks": track_count,
                })
        if results["next"]:
            results = sp.next(results)
        else:
            results = None
    return playlists


def save_playlists_csv(playlists, out_dir=None):
    """Save playlists to my_playlists.csv. Returns path."""
    out_dir = out_dir or config.get_output_dir()
    df = pd.DataFrame(playlists).sort_values(by="tracks", ascending=False)
    path = os.path.join(out_dir, "my_playlists.csv")
    df.to_csv(path, index=False)
    return path
